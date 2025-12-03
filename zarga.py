import os
import sys
import time
import random
import subprocess
import re
import json
from colorama import init, Fore, Back, Style

# Global variable to hold the active Tailscale Funnel process
_active_funnel_process = None

# --- Tailscale Process Management ---
def kill_tailscale_processes():
    print(f"{Fore.YELLOW}[*] Attempting to terminate all active Tailscale processes...{Style.RESET_ALL}")
    try:
        if sys.platform == "win32":
            # For Windows: Use taskkill
            subprocess.run(["taskkill", "/IM", "tailscale.exe", "/F"], check=False, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["taskkill", "/IM", "tailscaled.exe", "/F"], check=False, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # For Linux/macOS: Use pkill
            subprocess.run(["pkill", "tailscale"], check=False, capture_output=True, text=True)
            subprocess.run(["pkill", "tailscaled"], check=False, capture_output=True, text=True)
        print(f"{Fore.GREEN}[+] All known Tailscale processes terminated (if any were running).{Style.RESET_ALL}")
    except FileNotFoundError:
        print(f"{Fore.YELLOW}[!] Taskkill/pkill command not found. Cannot force terminate Tailscale processes.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Error terminating Tailscale processes: {str(e)}{Style.RESET_ALL}")

# --- Virtual Environment Activation Logic ---
venv_name = "zarga.dob"

if sys.platform == "win32":
    venv_python = os.path.join(venv_name, "Scripts", "python.exe")
else:
    venv_python = os.path.join(venv_name, "bin", "python3") # Use python3 for Linux/macOS

# Check if the script is already running within the virtual environment
# sys.real_prefix is set by venv, sys.base_prefix is original python prefix
if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
    print(f"[INFO] Activating virtual environment '{venv_name}'...")
    if os.path.exists(venv_python):
        # Re-run the current script using the venv's python
        try:
            subprocess.run([venv_python] + sys.argv, check=True)
            sys.exit(0) # Exit the current script after re-running in venv
        except KeyboardInterrupt:
            print("\n[INFO] Installation process interrupted by user. Exiting cleanly.")
            sys.exit(0) # Exit cleanly on Ctrl+C
        except Exception as e:
            print(f"[ERROR] Failed to re-run script in virtual environment: {e}")
            print("[ERROR] Please activate the virtual environment manually and try again:")
            if sys.platform == "win32":
                print(f"    {venv_name}\\Scripts\\activate")
            else:
                print(f"    source {venv_name}/bin/activate")
            sys.exit(1)
    else:
        print(f"[INFO] Virtual environment '{venv_name}' not found. Running install.py to set it up...")
        try:
            subprocess.run([sys.executable, "install.py"], check=True)
            # After installation, re-run zarga.py using the newly created venv
            print(f"[INFO] Virtual environment '{venv_name}' created. Re-running zarga.py in venv...")
            subprocess.run([venv_python] + sys.argv, check=True)
            sys.exit(0) # Exit the current script after successful re-run in venv
        except Exception as e:
            print(f"[ERROR] Failed to run install.py or re-run zarga.py in venv: {e}")
            print("[CRITICAL] Please ensure install.py is in the same directory and try again.")
            sys.exit(1)
# --- End of Virtual Environment Activation Logic ---

# Initialize colorama
init(autoreset=True)

# Funny hacker phrases
hacker_quotes = [
    "I'm not a hacker, I'm a digital locksmith.",
    "In a world full of 1's and 0's, I am the 2.",
    "I don't break systems, I just find creative ways to enter them.",
    "Firewalls are just speed bumps on the information highway.",
    "Passwords are like underwear: don't share them, change them often.",
    "There are 10 types of people in this world: those who understand binary and those who don't.",
    "It's not a bug, it's an undocumented feature.",
    "I don't always test my code, but when I do, I do it in production.",
    "My code doesn't have bugs, it just develops random features.",
    "Keep calm and <script>alert('hacked!')</script>",
    "The best place to hide a body is page 2 of Google search results.",
    "Programming is like sex: one mistake and you have to support it for the rest of your life.",
    "I'm not anti-social, I'm just not user friendly."
]

# Matrix effect characters
matrix_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%^&*"

# Brand color schemes
brand_colors = {
    "facebook": Fore.BLUE,
    "instagram": Fore.MAGENTA + Style.BRIGHT,
    "github": Fore.WHITE,
    "google": lambda text: f"{Fore.BLUE}G{Fore.RED}o{Fore.YELLOW}o{Fore.BLUE}g{Fore.GREEN}l{Fore.RED}e",
    "microsoft": lambda text: f"{Fore.BLUE}M{Fore.GREEN}i{Fore.RED}c{Fore.YELLOW}r{Fore.BLUE}o{Fore.GREEN}s{Fore.RED}o{Fore.YELLOW}f{Fore.BLUE}t",
    "netflix": Fore.RED + Style.BRIGHT,
    "X": Fore.CYAN + Style.BRIGHT,
    "twitter": Fore.CYAN
}

# New ASCII logo in red
ZARGA_LOGO = f"""{Fore.RED}
                       _ '                  ,.-:~:-.                .:'/*/'`:,·:~·–:.,                            __'                          ,.-:~:-.            
     /:¯:'`:*:^:*:´':¯::/'`;'             /':::::::::'`,             /::/:/:::/:::;::::::/`':.,'               ,.·:'´::::::::`'·-.                 /':::::::::'`,          
    /:: :: : : : : : :::/::'/            /;:-·~·-:;':::',          /·*'`·´¯'`^·-~·:–-'::;:::'`;            '/::::::::::::::::::';              /;:-·~·-:;':::',         
  ,´¯ '` * ^ * ´' ¯   '`;/    '       ,'´          '`:;::`,        '\\                       '`;::'i'         /;:· '´ ¯¯  `' ·-:::/'            ,'´          '`:;::`,       
  '`,                  ,·'   '         /                `;:\\         '`;        ,– .,        'i:'/        /.'´      _         ';/' '          /                `;:\\      
     '`*^*'´;       .´         '    ,'                   '`,::;         i       i':/:::';       ;/'       ,:     ,:'´::;'`·.,_.·'´.,    '     ,'                   '`,::;    
          .´     .'      _   ' '   i'       ,';´'`;         '\\:::', '     i       i/:·'´       ,:''        /     /':::::/;::::_::::::::;'     i'       ,';´'`;         '\\:::', '
       .´      ,'´~:~/:::/`:,  ,'        ;' /´:`';         ';:::'i'     '; '    ,:,     ~;'´:::'`:,   ,'     ;':::::'/·´¯     ¯'`·;:::¦'  ,'        ;' /´:`';         ';:::'i'
     .´      ,'´::::::/:::/:::'i' ;        ;/:;::;:';         ',:::;     'i      i:/\\       `;::::/:'`;''i     ';:::::::\\             ';:';'  ;        ;/:;::;:';         ',:::;
   ,'        '*^~·~*'´¯'`·;:/ 'i        '´        `'         'i::'/      ;     ;/   \\       '`:/::::/' ;      '`·:;:::::`'*;:'´      |/'  'i        '´        `'         'i::'/
  /                        ,'/  ¦       '/`' *^~-·'´\\         ';'/'‚      ';   ,'       \\         '`;/'   \\          '`*^*'´         /'  ' ¦       '/`' *^~-·'´\\         ';'/'‚
 ';                      ,.´    '`., .·´              `·.,_,.·´  ‚       `'*´          '`~·-·^'´        `·.,               ,.-·´      '`., .·´              `·.,_,.·´  ‚
   '`*^~–––––-·~^'´                                                                                    '`*^~·~^*'´                                              
{Style.RESET_ALL}"""

# Fix for input handling without msvcrt
def get_single_key():
    """Get a single keypress from the user, works on all platforms"""
    try:
        # Try to use msvcrt for Windows
        import msvcrt
        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
        print(key)
        return key
    except (ImportError, AttributeError):
        # Fallback for non-Windows systems
        try:
            # Try to use tty for Unix
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1).lower()
                print(key)
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (ImportError, AttributeError, termios.error):
            # Ultimate fallback - use input
            key = input().lower()
            if key:
                return key[0]
            return ''

def matrix_effect(duration=2):
    """Display a Matrix-like falling character effect"""
    width = os.get_terminal_size().columns
    height = os.get_terminal_size().lines
    
    # Store screen content to restore later
    os.system('cls' if os.name == 'nt' else 'clear')
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # Print random characters at random positions
        x = random.randint(0, width-1)
        y = random.randint(0, height-5)  # Leave space at bottom
        char = random.choice(matrix_chars)
        
        # Position cursor and print character
        print(f"\033[{y};{x}H{Fore.GREEN}{char}{Style.RESET_ALL}", end='', flush=True)
        time.sleep(0.001)
    
    os.system('cls' if os.name == 'nt' else 'clear')

def glitch_text(text):
    """Add glitch effect to text"""
    glitch_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/`~"
    glitched = ""
    for char in text:
        glitched += char
        # 10% chance to add a glitch character
        if random.random() < 0.1:
            glitched += random.choice(glitch_chars)
    return glitched

def type_writer(text, delay=0.03):
    """Display text with typewriter effect"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def cyber_loading(message="INITIALIZING", duration=2):
    """Display a cyber-style loading animation"""
    frames = [
        "[■□□□□□□□□□]",
        "[■■□□□□□□□□]",
        "[■■■□□□□□□□]",
        "[■■■■□□□□□□]",
        "[■■■■■□□□□□]",
        "[■■■■■■□□□□]",
        "[■■■■■■■□□□]",
        "[■■■■■■■■□□]",
        "[■■■■■■■■■□]",
        "[■■■■■■■■■■]"
    ]
    
    start_time = time.time()
    i = 0
    while time.time() - start_time < duration:
        i = (i + 1) % len(frames)
        sys_status = random.choice(["SCANNING", "CONNECTING", "ROUTING", "ENCRYPTING", "DECRYPTING"])
        loading_text = f"{Fore.GREEN}{frames[i]} {message}... {Fore.CYAN}{random.randint(10, 99)}% {Fore.YELLOW}[{sys_status}]{Style.RESET_ALL}"
        print(f"\r{loading_text}", end="", flush=True)
        time.sleep(0.1)
    
    print(f"\r{Fore.GREEN}[■■■■■■■■■■] {message} COMPLETE! {Fore.CYAN}100%{Style.RESET_ALL}")

def display_logo():
    # Display the new logo
    print(ZARGA_LOGO)
    
    # Add random hacker quote
    print(f"\n{Fore.YELLOW}{random.choice(hacker_quotes)}{Style.RESET_ALL}\n")
    
    # System status messages
    messages = [
        "Tool created by (ZARGA) , (JA3KA)",
        "Version: 0.7.5V (DEMO)",
        "For educational purposes only.",
    ]
    
    instagram_handles = [
        "@https://www.instagram.com/kemoj4b1/  zarga",
        "@https://www.instagram.com/_k.alrifa3i_/  JA3KA"
    ]
    
    # Print initial messages
    for msg in messages:
        print(f"{Fore.GREEN}>> {Fore.CYAN}{msg}{Style.RESET_ALL}")
        time.sleep(0.2)

    # Print Instagram handles
    for handle in instagram_handles:
        print(f"{Fore.GREEN}>> {Fore.MAGENTA}{handle}{Style.RESET_ALL}") # Using MAGENTA for handles for distinction
        time.sleep(0.2)

    print()

def find_directories_with_launcher():
    """Find directories that contain launcher.py (including subdirectories)"""
    directories = []
    launcher_paths = {}
    
    # First look for directories in the current directory
    for item in os.listdir('.'):
        if os.path.isdir(item) and item != "logs":
            # Check if this directory contains launcher.py directly
            launcher_path = os.path.join(item, "launcher.py")
            if os.path.exists(launcher_path):
                directories.append(item)
                launcher_paths[item] = launcher_path
            else:
                # Check for launcher.py in subdirectories
                for root, dirs, files in os.walk(item):
                    if "launcher.py" in files:
                        # Use the top-level directory name with path to launcher.py
                        directories.append(item)
                        launcher_paths[item] = os.path.join(root, "launcher.py")
                        break
    
    # Sort directories alphabetically
    directories.sort()
    
    # Ensure we have at most 8 items
    return directories[:8] if len(directories) > 8 else directories, launcher_paths

def check_tailscale_status():
    """Checks if tailscale is running and connected (tailscale up)."""
    print(f"{Fore.YELLOW}[*] Checking Tailscale status...{Style.RESET_ALL}")
    try:
        status_command = ["tailscale", "status", "--json"]
        status_process = subprocess.run(status_command, capture_output=True, text=True, encoding='utf-8', check=True)
        status_output = status_process.stdout
        status_json = json.loads(status_output)

        if "BackendState" in status_json and status_json["BackendState"] == "Running":
            if "Self" in status_json and "Online" in status_json["Self"] and status_json["Self"]["Online"]:
                print(f"{Fore.GREEN}[+] Tailscale is UP and connected!{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Tailscale backend is running, but not yet online/connected.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[!] Tailscale is DOWN. Please run 'tailscale up' to connect.{Style.RESET_ALL}")
    except FileNotFoundError:
        print(f"{Fore.RED}[!] Tailscale command not found. Please ensure Tailscale is installed and in your PATH.{Style.RESET_ALL}")
    except json.JSONDecodeError:
        print(f"{Fore.RED}[!] Error parsing Tailscale status JSON output. Tailscale might not be logged in or running.{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}[!] Error running tailscale status: {e.stderr}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] An unexpected error occurred while checking Tailscale status: {str(e)}{Style.RESET_ALL}")
    print()

def start_tailscale_funnel_and_get_url(port):
    """Starts tailscale funnel on the given port in the background and attempts to capture its URL."""
    global _active_funnel_process
    print(f"{Fore.YELLOW}[*] Starting Tailscale Funnel on port {port} in background...{Style.RESET_ALL}")
    funnel_url = "N/A"

    try:
        command_args = ["tailscale", "funnel", str(port)]
        if os.name == 'nt': # Windows
            _active_funnel_process = subprocess.Popen(["start", "/b", "tailscale", "funnel", str(port)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else: # Linux/macOS
            _active_funnel_process = subprocess.Popen(["setsid"] + command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Give the funnel some time to start and for status to update
        start_time = time.time()
        while time.time() - start_time < 15: # Increased timeout to 15 seconds for status to update
            try:
                status_result = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, encoding='utf-8', timeout=5)
                status_json = json.loads(status_result.stdout)
                
                # Check for Self.DNSName and construct URL
                if 'Self' in status_json and 'DNSName' in status_json['Self']:
                    dns_name = status_json['Self']['DNSName']
                    # Assuming the funnel URL is typically constructed as DNSName:port
                    # Tailscale funnel URLs are usually https://<DNSName>/ (if no explicit port specified)
                    # For specific ports, it's typically https://<DNSName>:<port>/
                    # Remove trailing dot if present
                    funnel_url = f"https://{dns_name.rstrip('.')}:{port}/"
                    print(f"{Fore.GREEN}[+] Tailscale Funnel URL captured: {funnel_url}{Style.RESET_ALL}")
                    break # Exit loop once URL is found
                
            except (json.JSONDecodeError, subprocess.TimeoutExpired, KeyError) as e:
                # print(f"{Fore.YELLOW}[!] Error polling Tailscale status: {e}. Retrying...{Style.RESET_ALL}")
                pass # Suppress frequent error messages
            time.sleep(1) # Wait before polling again

        if funnel_url == "N/A":
            print(f"{Fore.YELLOW}[!] Tailscale Funnel URL not found in status within timeout.{Style.RESET_ALL}")
            if _active_funnel_process and _active_funnel_process.poll() is None:
                print(f"{Fore.YELLOW}[*] Terminating unresponsive Tailscale Funnel process...{Style.RESET_ALL}")
                _active_funnel_process.terminate()
                try:
                    _active_funnel_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    _active_funnel_process.kill()
                _active_funnel_process = None
            print(f"{Fore.YELLOW}[*] Resetting Tailscale Funnel after failure to get URL...{Style.RESET_ALL}")
            subprocess.run(["tailscale", "funnel", "reset"], capture_output=True, text=True)


    except FileNotFoundError:
        print(f"{Fore.RED}[!] Tailscale command not found. Please ensure Tailscale is installed and in your PATH.{Style.RESET_ALL}")
        funnel_url = "N/A"
    except Exception as e:
        print(f"{Fore.RED}[!] Error during Tailscale Funnel startup: {str(e)}{Style.RESET_ALL}")
        funnel_url = "N/A"

    return funnel_url

def get_port_from_launcher_file(launcher_path):
    """
    Attempts to extract a port number from a launcher.py file.
    """
    try:
        with open(launcher_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Common patterns for port numbers
        # 1. port=XXXXX or port= XXXXX
        # 2. host='0.0.0.0', port=XXXXX
        # 3. Server starting on http://localhost:XXXXX
        # 4. 'XXXXX' (as a string literal)
        patterns = [
            r"port\s*=\s*(\d+)",
            r"localhost:(\d+)",
            r"127\.0\.0\.1:(\d+)",
            r"Server starting on http://localhost:(\d+)",
            r"[\'\"](\d{4,5})[\'\"]" # Match 4 or 5 digit numbers in quotes (e.g. '8000')
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1) # Return the captured group (the port number)
    except Exception as e:
        # print(f"{Fore.RED}Error reading {launcher_path}: {e}{Style.RESET_ALL}")
        pass

    # If no port found in launcher.py, check minimal_app.py or app.py in the same directory
    launcher_dir = os.path.dirname(launcher_path)
    additional_files = ["minimal_app.py", "app.py"]

    for extra_file in additional_files:
        extra_file_path = os.path.join(launcher_dir, extra_file)
        if os.path.exists(extra_file_path):
            try:
                with open(extra_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Use the same patterns to search in the additional file
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        return match.group(1) # Return the captured group (the port number)
            except Exception as e:
                # print(f"{Fore.RED}Error reading {extra_file_path}: {e}{Style.RESET_ALL}")
                pass

    return "N/A" # Return "N/A" if no port found or error

def colored_filename(filename):
    """Apply appropriate color to filename based on brand"""
    base_name = os.path.basename(filename).lower()
    
    for brand, color in brand_colors.items():
        if brand in base_name:
            if callable(color):
                return color(filename)
            else:
                return f"{color}{filename}{Style.RESET_ALL}"
    
    # Default color for non-branded files
    return f"{Fore.WHITE}{filename}{Style.RESET_ALL}"

def animate_text(text, delay=0.01):
    """Animate text typing"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def execute_launcher(directory, launcher_paths):
    """Execute the launcher.py file in the given directory"""
    launcher_path = launcher_paths.get(directory, os.path.join(directory, "launcher.py"))
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}EXECUTING LAUNCHER: {colored_filename(launcher_path)}{Style.RESET_ALL}")
    
    # Show fancy animation
    hack_messages = [
        "INITIALIZING LAUNCHER",
        "CONFIGURING ENVIRONMENT", 
        "BYPASSING SECURITY",
        "SETTING UP PARAMETERS",
        "PREPARING EXECUTION"
    ]
    
    for msg in hack_messages:
        print(f"\r{Fore.GREEN}>> {Fore.YELLOW}{msg}...{Style.RESET_ALL}", end="", flush=True)
        time.sleep(0.3)
    
    print(f"\r{Fore.GREEN}>> {Fore.CYAN}LAUNCHER READY. EXECUTING NOW!{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Save current directory
    current_dir = os.getcwd()
    
    launcher_process = None # Initialize process variable
    try:
        # Change to the directory containing launcher.py
        launcher_dir = os.path.dirname(launcher_path)
        os.chdir(launcher_dir)
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██████  ███████ ███    ███  ██████ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██   ██ ██      ████  ████ ██    ██ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██████  █████   ██ ████ ██ ██    ██ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██   ██ ██      ██  ██  ██ ██    ██ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██   ██ ███████ ██      ██  ██████ {Style.RESET_ALL}")
        print(f"{Fore.CYAN}          {directory.upper()} MODULE {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}          Version: zarga 0.7.1{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        
        # Run the launcher.py script using Popen to control it
        launcher_process = subprocess.Popen([sys.executable, "launcher.py"])
        
        # Keep zarga.py alive while launcher.py is running
        # Catch KeyboardInterrupt here to stop the child process and return to main menu
        try:
            while launcher_process.poll() is None: # None means process is still running
                time.sleep(0.5) # Prevent busy-waiting
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] TERMINATING {directory.upper()} MODULE...{Style.RESET_ALL}")
            if launcher_process.poll() is None: # Check if it's still running before terminating
                launcher_process.terminate()
                launcher_process.wait() # Wait for it to actually terminate
            print(f"{Fore.GREEN}[+] {directory.upper()} MODULE TERMINATED. {Style.RESET_ALL}")
            # This KeyboardInterrupt is handled, so it doesn't propagate to main()

        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}EXECUTION COMPLETE - PRESS ENTER TO RETURN TO MAIN MENU{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        
    except Exception as e:
        print(f"\n{Fore.RED}[!] ERROR EXECUTING LAUNCHER: {str(e)}{Style.RESET_ALL}")
    
    finally:
        # Ensure the launcher process is terminated if it's still running for any reason
        if launcher_process and launcher_process.poll() is None:
            print(f"\n{Fore.YELLOW}[!] FORCIBLY TERMINATING {directory.upper()} MODULE...{Style.RESET_ALL}")
            launcher_process.terminate()
            launcher_process.wait()
            print(f"{Fore.GREEN}[+] {directory.upper()} MODULE FORCIBLY TERMINATED. {Style.RESET_ALL}")

        # Return to the original directory
        os.chdir(current_dir)
        
        # Wait for user input before returning to menu
        input(f"\n{Fore.CYAN}Press ENTER to return to main menu...{Style.RESET_ALL}")

def execute_port_changer():
    """Execute the port_changer.py script"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}EXECUTING PORT CHANGER: {colored_filename('port_changer.py')}{Style.RESET_ALL}")
    
    # Show fancy animation
    hack_messages = [
        "INITIALIZING PORT CHANGER",
        "CONFIGURING NETWORK INTERFACES",
        "SCANNING FOR OPEN PORTS",
        "PREPARING PORT ALTERATION",
        "LAUNCHING APPLICATION"
    ]
    
    for msg in hack_messages:
        print(f"\r{Fore.GREEN}>> {Fore.YELLOW}{msg}...{Style.RESET_ALL}", end="", flush=True)
        time.sleep(0.3)
    
    print(f"\r{Fore.GREEN}>> {Fore.CYAN}PORT CHANGER READY. EXECUTING NOW!{Style.RESET_ALL}")
    time.sleep(0.5)

    # Save current directory
    current_dir = os.getcwd()

    port_changer_process = None # Initialize process variable
    try:
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██████  ███████ ███    ███  ██████ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██   ██ ██      ████  ████ ██    ██ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██████  █████   ██ ████ ██ ██    ██ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██   ██ ██      ██  ██  ██ ██    ██ {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}        ██   ██ ███████ ██      ██  ██████ {Style.RESET_ALL}")
        print(f"{Fore.CYAN}          PORT CHANGER MODULE {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}          Version: zarga 0.7.1{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")

        # Run the port_changer.py script using Popen to control it
        port_changer_process = subprocess.Popen([sys.executable, "port_changer.py"])

        # Keep zarga.py alive while port_changer.py is running
        try:
            while port_changer_process.poll() is None:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] TERMINATING PORT CHANGER MODULE...{Style.RESET_ALL}")
            if port_changer_process.poll() is None:
                port_changer_process.terminate()
                port_changer_process.wait()
            print(f"{Fore.GREEN}[+] PORT CHANGER MODULE TERMINATED. {Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}EXECUTION COMPLETE - PRESS ENTER TO RETURN TO MAIN MENU{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")

    except Exception as e:
        print(f"\n{Fore.RED}[!] ERROR EXECUTING PORT CHANGER: {str(e)}{Style.RESET_ALL}")

    finally:
        if port_changer_process and port_changer_process.poll() is None:
            print(f"\n{Fore.YELLOW}[!] FORCIBLY TERMINATING PORT CHANGER MODULE...{Style.RESET_ALL}")
            port_changer_process.terminate()
            port_changer_process.wait()
            print(f"{Fore.GREEN}[+] PORT CHANGER MODULE FORCIBLY TERMINATED. {Style.RESET_ALL}")

        os.chdir(current_dir)
        input(f"\n{Fore.CYAN}Press ENTER to return to main menu...{Style.RESET_ALL}")

def main():
    try:
        kill_tailscale_processes() # Kill Tailscale processes at start
        # Initial matrix effect
        matrix_effect(1.5)
        
        # Show loading screen
        cyber_loading("SYSTEM BOOT", 3)
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Ask if the user will use the program wisely
        type_writer(f"{Fore.RED}WARNING: {Fore.YELLOW}THIS SYSTEM IS FOR AUTHORIZED USERS ONLY")
        type_writer(f"{Fore.WHITE}Will you use this program wisely? (y/n): ", 0.03)
        
        # Get user input without requiring Enter - using our new cross-platform function
        while True:
            key = get_single_key()
            if key == 'y':
                break
            elif key == 'n':
                type_writer(f"\n{Fore.RED}ACCESS DENIED. SYSTEM SHUTDOWN INITIATED.{Style.RESET_ALL}")
                time.sleep(1)
                sys.exit()
            elif key in ['q', '\x03']:  # q or Ctrl+C
                print("\nEXITING SYSTEM...")
                time.sleep(0.5)
                sys.exit()
        
        # Clear screen and show cyber loading
        os.system('cls' if os.name == 'nt' else 'clear')
        cyber_loading("ACCESS VERIFICATION", 2)
        
        # Matrix effect transition
        matrix_effect(1)
        
        # Clear screen and display logo
        os.system('cls' if os.name == 'nt' else 'clear')
        display_logo()
        
        # Get directories with launcher.py
        directories, launcher_paths = find_directories_with_launcher()
        
        if not directories:
            print(f"{Fore.RED}[!] NO LAUNCHER MODULES FOUND!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please make sure that launcher.py files exist in the subdirectories.{Style.RESET_ALL}")
            input("Press Enter to exit...")
            sys.exit()
        
        # Display numbers with directory names
        print(f"{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}AVAILABLE LAUNCHER MODULES:{Style.RESET_ALL}\n")
        for i, directory in enumerate(directories, 1):
            colored_dir = colored_filename(directory)
            launcher_loc = "DIRECT" if launcher_paths[directory] == os.path.join(directory, "launcher.py") else "SUBDIR"
            port_info = get_port_from_launcher_file(launcher_paths[directory])
            print(f"{Fore.GREEN}[{Fore.CYAN}{i}{Fore.GREEN}] {colored_dir} {Fore.YELLOW}[LAUNCHER {launcher_loc}] [PORT: {port_info}]{Style.RESET_ALL}")
        
        # Move the PORT CHANGER option outside the loop to avoid repetition
        print(f"{Fore.GREEN}[{Fore.CYAN}P{Fore.GREEN}] {Fore.YELLOW}PORT CHANGER{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}SELECT MODULE NUMBER TO EXECUTE: {Style.RESET_ALL}", end="", flush=True)
        
        # Handle number input without pressing enter - using our new cross-platform function
        while True:
            key = get_single_key()
            
            if key.isdigit() and 1 <= int(key) <= len(directories):
                selected = int(key)
                selected_directory = directories[selected-1]
                port_info = get_port_from_launcher_file(launcher_paths[selected_directory])

                print(f"\n{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}Selected module: {colored_filename(selected_directory)}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[{Fore.CYAN}1{Fore.GREEN}] {Fore.WHITE}Launch via Localhost{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[{Fore.CYAN}2{Fore.GREEN}] {Fore.WHITE}Launch via Tailscale Funnel (Port: {port_info}){Style.RESET_ALL}")
                print(f"{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}Select launch option: {Style.RESET_ALL}", end="", flush=True)

                while True:
                    launch_key = get_single_key()
                    if launch_key == '1':
                        # Launch via Localhost
                        execute_launcher(selected_directory, launcher_paths)
                        break
                    elif launch_key == '2':
                        # Launch via Tailscale Funnel
                        global _active_funnel_process
                        
                        # Temporarily start and reset funnel to get URL
                        print(f"{Fore.CYAN}[DEBUG] Port info before funnel: {port_info}{Style.RESET_ALL}") # Added for debugging
                        funnel_url = start_tailscale_funnel_and_get_url(port_info)

                        if funnel_url != "N/A":
                            print(f"\n{Fore.GREEN}Your Tailscale Funnel URL is: {Fore.CYAN}{funnel_url}{Style.RESET_ALL}")
                            input(f"{Fore.CYAN}Press ENTER to launch module...{Style.RESET_ALL}")
                            
                            # Start the actual long-running Tailscale Funnel in background
                            print(f"{Fore.YELLOW}[*] Starting actual Tailscale Funnel on port {port_info} in background...{Style.RESET_ALL}")
                            command_args = ["tailscale", "funnel", str(port_info)]
                            if os.name == 'nt': # Windows
                                # Use `start /b` to run the command in a new, unattached window
                                # shell=True is required for `start /b`
                                # Use `CREATE_NO_WINDOW` to prevent a console window from popping up
                                _active_funnel_process = subprocess.Popen(["start", "/b", "tailscale", "funnel", str(port_info)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                            else: # Linux/macOS
                                # Use `setsid` to run in a new session, detached from the controlling terminal
                                _active_funnel_process = subprocess.Popen(["setsid"] + command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            
                            execute_launcher(selected_directory, launcher_paths)
                            
                            # After module execution, terminate the funnel process
                            if _active_funnel_process and _active_funnel_process.poll() is None:
                                print(f"\n{Fore.YELLOW}[*] Terminating Tailscale Funnel...{Style.RESET_ALL}")
                                _active_funnel_process.terminate()
                                try:
                                    _active_funnel_process.wait(timeout=5)
                                except subprocess.TimeoutExpired:
                                    _active_funnel_process.kill()
                                    print(f"{Fore.YELLOW}[!] Tailscale Funnel process forcibly terminated.{Style.RESET_ALL}\n")
                                _active_funnel_process = None
                            
                            print(f"{Fore.YELLOW}[*] Resetting Tailscale Funnel after module execution...{Style.RESET_ALL}")
                            subprocess.run(["tailscale", "funnel", "reset"], capture_output=True, text=True)
                        else:
                            print(f"{Fore.RED}[!] Failed to get Tailscale Funnel URL. Launching via Localhost instead.{Style.RESET_ALL}")
                            execute_launcher(selected_directory, launcher_paths)
                        
                        break
                    else:
                        print(f"\r{Fore.RED}Invalid option. Please enter '1' or '2'.{Style.RESET_ALL}", end="", flush=True)
                
                # Return to main menu with matrix transition
                matrix_effect(1)
                os.system('cls' if os.name == 'nt' else 'clear')
                display_logo()
                
                # Display modules again
                print(f"{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}AVAILABLE LAUNCHER MODULES:{Style.RESET_ALL}\n")
                for i, directory in enumerate(directories, 1):
                    colored_dir = colored_filename(directory)
                    launcher_loc = "DIRECT" if launcher_paths[directory] == os.path.join(directory, "launcher.py") else "SUBDIR"
                    port_info = get_port_from_launcher_file(launcher_paths[directory])
                    print(f"{Fore.GREEN}[{Fore.CYAN}{i}{Fore.GREEN}] {colored_dir} {Fore.YELLOW}[LAUNCHER {launcher_loc}] [PORT: {port_info}]{Style.RESET_ALL}")
                
                print(f"{Fore.GREEN}[{Fore.CYAN}P{Fore.GREEN}] {Fore.YELLOW}PORT CHANGER{Style.RESET_ALL}")
                
                print(f"\n{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}SELECT MODULE NUMBER TO EXECUTE: {Style.RESET_ALL}", end="", flush=True)
            
            elif key == 'p': # Handle 'p' for port_changer.py
                execute_port_changer()
                
                # Return to main menu with matrix transition
                matrix_effect(1)
                os.system('cls' if os.name == 'nt' else 'clear')
                display_logo()
                
                # Display numbers with directory names again
                print(f"{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}AVAILABLE LAUNCHER MODULES:{Style.RESET_ALL}\n")
                for i, directory in enumerate(directories, 1):
                    colored_dir = colored_filename(directory)
                    launcher_loc = "DIRECT" if launcher_paths[directory] == os.path.join(directory, "launcher.py") else "SUBDIR"
                    port_info = get_port_from_launcher_file(launcher_paths[directory])
                    print(f"{Fore.GREEN}[{Fore.CYAN}{i}{Fore.GREEN}] {colored_dir} {Fore.YELLOW}[LAUNCHER {launcher_loc}] [PORT: {port_info}]{Style.RESET_ALL}")
                
                # Move the PORT CHANGER option outside the loop to avoid repetition
                print(f"{Fore.GREEN}[{Fore.CYAN}P{Fore.GREEN}] {Fore.YELLOW}PORT CHANGER{Style.RESET_ALL}")
                
                print(f"\n{Fore.GREEN}[{Fore.CYAN}*{Fore.GREEN}] {Fore.WHITE}SELECT MODULE NUMBER TO EXECUTE: {Style.RESET_ALL}", end="", flush=True)
            
            elif key in ['q', '\x03']:  # q or Ctrl+C
                print("\nEXITING SYSTEM...")
                time.sleep(0.5)
                matrix_effect(1)
                sys.exit()
    
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}SYSTEM INTERRUPT DETECTED. SHUTTING DOWN.{Style.RESET_ALL}")
        kill_tailscale_processes() # Kill Tailscale processes on interrupt
        matrix_effect(0.5)
        sys.exit()
    finally:
        kill_tailscale_processes() # Kill Tailscale processes at end (ensure cleanup)

if __name__ == "__main__":
    main()
