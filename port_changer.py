import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import mimetypes
import argparse
import sys
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored terminal output
init()

class PortChanger:
    """Core functionality for port changing, independent of UI"""
    def __init__(self):
        self.files_changed = 0
        self.occurrences_changed = 0
        self.log_callback = print  # Default to print to console
    
    def set_log_callback(self, callback):
        """Set callback function for logging"""
        self.log_callback = callback
    
    def log_message(self, message):
        """Log message using the callback"""
        self.log_callback(message)
    
    def is_binary_file(self, file_path):
        """Check if a file is binary"""
        try:
            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type and not mime_type.startswith(('text/', 'application/json', 'application/xml')):
                return True
            
            # Check file content
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk  # Binary files often contain null bytes
        except Exception:
            return True
    
    def change_ports(self, folder_path, old_port, new_port, file_types=None):
        """
        Change port numbers in files
        
        Args:
            folder_path: Path to search in
            old_port: Port number to replace
            new_port: New port number
            file_types: List of file extensions to process, None for all types
        
        Returns:
            Tuple of (files_changed, occurrences_changed)
        """
        # Validate inputs
        if not folder_path or not os.path.isdir(folder_path):
            self.log_message(f"{Fore.RED}Error: Invalid directory{Style.RESET_ALL}")
            return 0, 0
        
        try:
            old_port_int = int(old_port)
            new_port_int = int(new_port)
            if old_port_int < 0 or new_port_int < 0 or old_port_int > 65535 or new_port_int > 65535:
                self.log_message(f"{Fore.RED}Error: Port number must be between 0 and 65535{Style.RESET_ALL}")
                return 0, 0
        except ValueError:
            self.log_message(f"{Fore.RED}Error: Port must be a valid integer{Style.RESET_ALL}")
            return 0, 0
        
        # Prepare file extensions to process
        extensions = []
        if file_types:
            extensions = file_types.lower().split(',')
            extensions = [ext.strip() for ext in extensions if ext.strip()]
        
        # Reset counters
        self.files_changed = 0
        self.occurrences_changed = 0
        
        # Start processing
        self.log_message(f"{Fore.CYAN}Searching directory: {folder_path}{Style.RESET_ALL}")
        self.log_message(f"{Fore.YELLOW}Changing port from {old_port} to {new_port}{Style.RESET_ALL}")
        self.log_message(f"{Fore.GREEN}Processing...{Style.RESET_ALL}")
        
        # Walk through directory
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file extension is in our list
                file_ext = os.path.splitext(file)[1].lower().lstrip('.')
                if not extensions or file_ext in extensions:
                    # Skip binary files
                    if self.is_binary_file(file_path):
                        continue
                    
                    try:
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Create patterns to match ports in different contexts
                        patterns = [
                            r'(:|=|\s+)' + re.escape(old_port) + r'(\s|,|;|$|\'|\"|\))',  # Common patterns like :3000, =3000, etc.
                            r'port\s*[=:]\s*' + re.escape(old_port),  # port=50000 or port: 50000
                            r'PORT\s*[=:]\s*' + re.escape(old_port),  # PORT=50000 or PORT: 50000
                            r'localhost:' + re.escape(old_port),  # localhost:50000
                            r'127\.0\.0\.1:' + re.escape(old_port),  # 127.0.0.1:50000
                        ]
                        
                        new_content = content
                        file_changed = False
                        occurrences = 0
                        
                        for pattern in patterns:
                            # Function to replace while preserving the surrounding characters
                            def replace_port(match):
                                nonlocal occurrences
                                occurrences += 1
                                if ':' in match.group(0):
                                    return match.group(0).replace(old_port, new_port)
                                elif '=' in match.group(0):
                                    return match.group(0).replace(old_port, new_port)
                                else:
                                    # General case
                                    return match.group(0).replace(old_port, new_port)
                            
                            # Apply the replacement
                            temp_content = re.sub(pattern, replace_port, new_content)
                            if temp_content != new_content:
                                new_content = temp_content
                                file_changed = True
                        
                        # If changes were made, write back to file
                        if file_changed:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            self.files_changed += 1
                            self.occurrences_changed += occurrences
                            
                            # Log the change
                            relative_path = os.path.relpath(file_path, folder_path)
                            self.log_message(f"{Fore.GREEN}Changed: {relative_path} ({occurrences} occurrences){Style.RESET_ALL}")
                    
                    except Exception as e:
                        self.log_message(f"{Fore.RED}Error processing file {file}: {str(e)}{Style.RESET_ALL}")
        
        # Show summary
        self.log_message(f"\n{Fore.CYAN}---- SUMMARY ----{Style.RESET_ALL}")
        if self.files_changed > 0:
            self.log_message(f"{Fore.GREEN}Changed {self.occurrences_changed} port occurrences in {self.files_changed} files{Style.RESET_ALL}")
        else:
            self.log_message(f"{Fore.YELLOW}No matches found for port {old_port}{Style.RESET_ALL}")
        
        return self.files_changed, self.occurrences_changed

    def change_port_in_single_file(self, file_path, old_port, new_port):
        """
        Change port number in a single specified file.
        
        Args:
            file_path: Path to the file to process
            old_port: Port number to replace
            new_port: New port number
        
        Returns:
            Tuple of (files_changed, occurrences_changed) for this single file (0 or 1, count)
        """
        self.files_changed = 0
        self.occurrences_changed = 0

        # Validate inputs
        if not os.path.isfile(file_path):
            self.log_message(f"{Fore.RED}Error: Invalid file path: {file_path}{Style.RESET_ALL}")
            return 0, 0
        
        try:
            old_port_int = int(old_port)
            new_port_int = int(new_port)
            if not (0 <= old_port_int <= 65535 and 0 <= new_port_int <= 65535):
                self.log_message(f"{Fore.RED}Error: Port number must be between 0 and 65535{Style.RESET_ALL}")
                return 0, 0
        except ValueError:
            self.log_message(f"{Fore.RED}Error: Port must be a valid integer{Style.RESET_ALL}")
            return 0, 0
        
        self.log_message(f"{Fore.CYAN}Processing file: {file_path}{Style.RESET_ALL}")
        self.log_message(f"{Fore.YELLOW}Changing port from {old_port} to {new_port}{Style.RESET_ALL}")
        
        if self.is_binary_file(file_path):
            self.log_message(f"{Fore.YELLOW}Skipping binary file: {file_path}{Style.RESET_ALL}")
            return 0, 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            patterns = [
                r'(:|=|\s+)' + re.escape(old_port) + r'(\s|,|;|$|\'|\"|\))',
                r'port\s*[=:]\s*' + re.escape(old_port),
                r'PORT\s*[=:]\s*' + re.escape(old_port),
                r'localhost:' + re.escape(old_port),
                r'127\.0\.0\.1:' + re.escape(old_port),
            ]
            
            new_content = content
            file_changed = False
            occurrences = 0
            
            for pattern in patterns:
                def replace_port(match):
                    nonlocal occurrences
                    occurrences += 1
                    return match.group(0).replace(old_port, new_port)
                
                temp_content = re.sub(pattern, replace_port, new_content)
                if temp_content != new_content:
                    new_content = temp_content
                    file_changed = True
            
            if file_changed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.files_changed = 1 # Only one file processed
                self.occurrences_changed = occurrences
                self.log_message(f"{Fore.GREEN}Changed: {file_path} ({occurrences} occurrences){Style.RESET_ALL}")
            else:
                self.log_message(f"{Fore.YELLOW}No matches found for port {old_port} in {file_path}{Style.RESET_ALL}")

            return self.files_changed, self.occurrences_changed
        
        except Exception as e:
            self.log_message(f"{Fore.RED}Error processing file {file_path}: {str(e)}{Style.RESET_ALL}")
            return 0, 0


class PortChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Port Changer")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize port changer
        self.port_changer = PortChanger()
        self.port_changer.set_log_callback(self.log_message)
        
        # Initialize variables
        self.folder_path = tk.StringVar()
        self.old_port = tk.StringVar()
        self.new_port = tk.StringVar()
        self.file_types = tk.StringVar(value="txt,html,js,py,json,xml,yml,yaml,cfg,conf,ini")
        
        # Create GUI
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="Port Changer Tool", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Folder selection
        folder_frame = tk.Frame(self.root, bg="#f0f0f0")
        folder_frame.pack(fill="x", padx=20, pady=5)
        
        folder_label = tk.Label(folder_frame, text="Select Folder:", width=15, anchor="w", bg="#f0f0f0")
        folder_label.pack(side="left")
        
        folder_entry = tk.Entry(folder_frame, textvariable=self.folder_path, width=40)
        folder_entry.pack(side="left", padx=5)
        
        browse_button = tk.Button(folder_frame, text="Browse", command=self.browse_folder, width=10)
        browse_button.pack(side="left")
        
        # Port inputs
        ports_frame = tk.Frame(self.root, bg="#f0f0f0")
        ports_frame.pack(fill="x", padx=20, pady=5)
        
        old_port_label = tk.Label(ports_frame, text="Old Port:", width=15, anchor="w", bg="#f0f0f0")
        old_port_label.pack(side="left")
        
        old_port_entry = tk.Entry(ports_frame, textvariable=self.old_port, width=20)
        old_port_entry.pack(side="left", padx=5)
        
        new_port_label = tk.Label(ports_frame, text="New Port:", width=15, anchor="w", bg="#f0f0f0")
        new_port_label.pack(side="left")
        
        new_port_entry = tk.Entry(ports_frame, textvariable=self.new_port, width=20)
        new_port_entry.pack(side="left")
        
        # File types
        file_types_frame = tk.Frame(self.root, bg="#f0f0f0")
        file_types_frame.pack(fill="x", padx=20, pady=5)
        
        file_types_label = tk.Label(file_types_frame, text="File Types:", width=15, anchor="w", bg="#f0f0f0")
        file_types_label.pack(side="left")
        
        file_types_entry = tk.Entry(file_types_frame, textvariable=self.file_types, width=60)
        file_types_entry.pack(side="left", padx=5)
        
        # Status output
        self.status_text = tk.Text(self.root, height=10, width=70)
        self.status_text.pack(padx=20, pady=10)
        self.status_text.config(state="disabled")
        
        # Buttons
        buttons_frame = tk.Frame(self.root, bg="#f0f0f0")
        buttons_frame.pack(fill="x", padx=20, pady=10)
        
        change_button = tk.Button(
            buttons_frame, 
            text="Change Port", 
            command=self.change_ports,
            bg="#4CAF50", 
            fg="white", 
            width=15, 
            height=2
        )
        change_button.pack(side="left", padx=10)
        
        clear_button = tk.Button(
            buttons_frame, 
            text="Clear", 
            command=self.clear_fields,
            bg="#f44336", 
            fg="white", 
            width=15, 
            height=2
        )
        clear_button.pack(side="left", padx=10)
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def log_message(self, message):
        # Remove ANSI color codes for GUI text display
        message = re.sub(r'\x1b\[\d+m', '', message)
        
        self.status_text.config(state="normal")
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state="disabled")
        self.root.update()
    
    def clear_log(self):
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", tk.END)
        self.status_text.config(state="disabled")
    
    def clear_fields(self):
        self.folder_path.set("")
        self.old_port.set("")
        self.new_port.set("")
        self.clear_log()
    
    def change_ports(self):
        folder_path = self.folder_path.get()
        old_port = self.old_port.get()
        new_port = self.new_port.get()
        file_types = self.file_types.get()
        
        self.clear_log()
        
        # Use the core functionality
        files_changed, occurrences_changed = self.port_changer.change_ports(
            folder_path, old_port, new_port, file_types
        )
        
        # Show GUI message
        if files_changed == 0:
            messagebox.showinfo("Completed", f"No occurrences of port {old_port} were found")
        else:
            messagebox.showinfo("Completed", f"Changed {occurrences_changed} occurrences of port {old_port} to {new_port} in {files_changed} files")


def run_interactive_mode():
    """Run interactive CLI version that prompts for inputs"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== PORT CHANGER TOOL ==={Style.RESET_ALL}\n")
    
    # Automatically get the directory where port_changer.py is located
    folder_path = os.path.dirname(os.path.abspath(__file__))
    print(f"{Fore.GREEN}Automatically processing current directory: {folder_path}{Style.RESET_ALL}")
    
    # Ask for old port
    while True:
        old_port = input(f"{Fore.YELLOW}Enter the old port number: {Style.RESET_ALL}").strip()
        try:
            old_port_int = int(old_port)
            if old_port_int < 0 or old_port_int > 65535:
                print(f"{Fore.RED}Error: Port must be between 0 and 65535{Style.RESET_ALL}")
                continue
            break
        except ValueError:
            print(f"{Fore.RED}Error: Port must be a valid integer{Style.RESET_ALL}")
    
    # Ask for new port
    while True:
        new_port = input(f"{Fore.YELLOW}Enter the new port number: {Style.RESET_ALL}").strip()
        try:
            new_port_int = int(new_port)
            if new_port_int < 0 or new_port_int > 65535:
                print(f"{Fore.RED}Error: Port must be between 0 and 65535{Style.RESET_ALL}")
                continue
            break
        except ValueError:
            print(f"{Fore.RED}Error: Port must be a valid integer{Style.RESET_ALL}")
    
    # Ask for file types (optional)
    default_types = "txt,html,js,py,json,xml,yml,yaml,cfg,conf,ini"
    file_types = input(f"{Fore.YELLOW}Enter file types to search (comma-separated) or press Enter for defaults [{default_types}]: {Style.RESET_ALL}").strip()
    if not file_types:
        file_types = default_types
    
    print(f"\n{Fore.MAGENTA}Starting port change process...{Style.RESET_ALL}\n")
    
    # Start port changing process
    port_changer = PortChanger()
    port_changer.change_ports(folder_path, old_port, new_port, file_types)
    
    # Ask if the user wants to run again
    while True:
        run_again = input(f"\n{Fore.CYAN}Do you want to run the program again? (y/n): {Style.RESET_ALL}").strip().lower()
        if run_again in ['y', 'yes']:
            run_interactive_mode()
            return
        elif run_again in ['n', 'no']:
            print(f"{Fore.GREEN}Program terminated. Goodbye!{Style.RESET_ALL}")
            return
        else:
            print(f"{Fore.RED}Please enter 'y' or 'n'{Style.RESET_ALL}")


def run_gui():
    """Run the GUI version of the application"""
    root = tk.Tk()
    app = PortChangerApp(root)
    root.mainloop()


def run_cli():
    """Run the command-line version of the application"""
    parser = argparse.ArgumentParser(description="Port Changer CLI Tool")
    parser.add_argument('-f', '--folder', type=str, help="Folder to search in")
    parser.add_argument('-sf', '--single-file', type=str, help="Single file to change port in")
    parser.add_argument('-o', '--old-port', type=str, required=True, help="Old port number")
    parser.add_argument('-n', '--new-port', type=str, required=True, help="New port number")
    parser.add_argument('-t', '--file-types', type=str, help="Comma-separated list of file extensions (e.g., txt,html,js)")
    
    args = parser.parse_args()
    
    port_changer = PortChanger()
    
    if args.single_file:
        port_changer.change_port_in_single_file(args.single_file, args.old_port, args.new_port)
    elif args.folder:
        port_changer.change_ports(args.folder, args.old_port, args.new_port, args.file_types)
    else:
        # If no folder or single file specified, default to current directory
        folder_path = os.path.dirname(os.path.abspath(__file__))
        print(f"{Fore.GREEN}No folder or single file specified. Automatically processing current directory: {folder_path}{Style.RESET_ALL}")
        port_changer.change_ports(folder_path, args.old_port, args.new_port, args.file_types)


if __name__ == "__main__":
    # Initialize mimetypes
    mimetypes.init()
    
    # Run CLI with appropriate mode detection
    if len(sys.argv) > 1: # If arguments are passed, assume CLI mode
        run_cli()
    else: # Otherwise, run GUI mode (or interactive mode as fallback)
        try:
            run_interactive_mode()
        except Exception as e:
            print(f"{Fore.RED}Error running GUI: {e}. Falling back to CLI mode if arguments are provided or exiting.{Style.RESET_ALL}")
            if len(sys.argv) > 1:
                run_cli()
            else:
                sys.exit(1) 