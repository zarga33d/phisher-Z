import subprocess
import sys
import os
import time

# ANSI color codes (simplified for direct use, as colorama might not be installed yet)
YELLOW = "\033[93m"
RESET = "\033[0m"

def run_command(command, message):
    print(f"\n[INFO] {message}")
    try:
        # Use shell=True for simpler command parsing on Windows for commands like 'activate'
        # For Linux commands, shell=True is generally fine but can have security implications if command is user-provided.
        # Here, commands are hardcoded, so it's okay.
        
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        
        # Stream stdout in real-time
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
        
        # Read remaining stderr (if any, though it's usually mixed with stdout)
        for line in process.stderr:
            sys.stderr.write(line)
            sys.stderr.flush()
            
        process.wait() # Wait for the process to finish
        
        if process.returncode != 0:
            print(f"[ERROR] Command failed with exit code {process.returncode}: {command}")
            return False
        
        return True
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during command execution: {e}")
        return False

def run_tailscale_up():
    print("\n[INFO] Running 'sudo tailscale up'...")
    print("[WARNING] This command might prompt you for your sudo password.")
    command = "sudo tailscale up"
    
    while True:
        process = None
        try:
            # Use subprocess.run to capture output easily
            result = subprocess.run(command, shell=True, check=False, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            # Print stdout and stderr immediately
            sys.stdout.write(result.stdout)
            sys.stdout.flush()
            if result.stderr:
                sys.stderr.write(result.stderr)
                sys.stderr.flush()
            
            login_url_found = False
            if "To authenticate, visit:" in result.stdout or "To authenticate, visit:" in result.stderr:
                login_url_found = True

            if login_url_found:
                print(f"\n{'-'*80}")
                print(f"  {YELLOW}ACTION REQUIRED: Please open the Tailscale login URL in your browser.{RESET}")
                print(f"  {YELLOW}The script will wait here until you complete the login (5-second retry).{RESET}")
                print(f"  {YELLOW}If you've already logged in, the script will proceed automatically.{RESET}")
                print(f"{'-'*80}\n")
                time.sleep(5) # Wait for 5 seconds before retrying
                continue # Retry the command
            elif result.returncode == 0:
                print("[INFO] 'tailscale up' completed without requiring a new login (likely already authenticated or successful).")
                return True # Success, break the loop
            else:
                print(f"[ERROR] 'sudo tailscale up' command failed with exit code {result.returncode}.")
                return False # Command failed, exit
            
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred during Tailscale setup: {e}")
            return False
        finally:
            if process and process.poll() is None: 
                process.terminate()

def main():
    venv_name = "zarga.dob"
    requirements_file = "requirements.txt"

    # 1. Create virtual environment
    if not run_command(f"python -m venv {venv_name}", f"Creating virtual environment '{venv_name}'..."):
        print("[CRITICAL] Failed to create virtual environment. Exiting.")
        sys.exit(1)

    # Determine the path to the Python executable within the virtual environment
    if sys.platform == "win32":
        venv_python_path = os.path.join(venv_name, "Scripts", "python.exe")
    else:
        venv_python_path = os.path.join(venv_name, "bin", "python3") # Use python3 for Linux/macOS

    if not os.path.exists(venv_python_path):
        print(f"[CRITICAL] Python executable not found in virtual environment at {venv_python_path}. Exiting.")
        sys.exit(1)

    # 2. Install requirements using the virtual environment's python and pip module
    if not run_command(f"{venv_python_path} -m pip install -r {requirements_file}", f"Installing packages from '{requirements_file}'..."):
        print("[CRITICAL] Failed to install packages. Exiting.")
        sys.exit(1)

    # 3. Verify installed packages using the virtual environment's python and pip module
    if not run_command(f"{venv_python_path} -m pip check", "Verifying installed packages..."):
        print("\n==================================================================")
        print("  ERROR: Some packages are not installed correctly or have issues!")
        print("==================================================================")
    else:
        print("\n===========================================")
        print("  All packages verified successfully!   ")
        print("===========================================")

    print(f"\n[INFO] Python packages installation and verification completed. You can activate the environment by running: {venv_name}\Scripts\activate (on Windows) or source {venv_name}/bin/activate (on Linux/macOS)")

    # Tailscale installation and setup (Linux specific)
    print("\n[INFO] Checking for Tailscale installation...")
    try:
        subprocess.run(["which", "tailscale"], check=True, capture_output=True, text=True)
        print("[INFO] Tailscale is already installed.")
    except subprocess.CalledProcessError:
        print("[INFO] Tailscale not found. Installing Tailscale...")
        if not run_command("curl -fsSL https://tailscale.com/install.sh | sh", "Running Tailscale installation script..."):
            print("[CRITICAL] Failed to install Tailscale. Please check your internet connection and try again. Exiting.")
            sys.exit(1)
        print("[INFO] Tailscale installed successfully.")

    if not run_tailscale_up(): # Use the new specialized function
        print("[CRITICAL] Failed to activate Tailscale. Exiting.")
        sys.exit(1)
    print("[SUCCESS] Tailscale is up and running.")

if __name__ == "__main__":
    main() 