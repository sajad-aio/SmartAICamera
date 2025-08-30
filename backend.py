#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face Recognition and Emotion Detection Backend
Integrates with the existing Jupyter notebook code
"""

import os
import cv2
import json
import time
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import face_recognition as fr
import base64
from io import BytesIO
from PIL import Image
import threading

# Try to import TensorFlow for emotion detection
try:
    from tensorflow.keras.models import load_model
    EMOTION_MODEL_AVAILABLE = True
except ImportError:
    print("TensorFlow not available. Emotion detection will be simulated.")
    EMOTION_MODEL_AVAILABLE = False

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configuration
USERS_PATH = "users"
EMOTION_LABELS = ['عصبانی', 'متنفر', 'ناراحت', 'ترسیده', 'شاد', 'متعجب', 'خنثی']

# Global variables
emotion_model = None
registered_users = {}
detection_history = []
camera = None
user_motion = 0
last_position = None
user_detected = False
user_detect_start = None
user_activation_time = 3
start_time = None
user_emotions = {}

class Camera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    def __del__(self):
        self.release()
        
    def release(self):
        if hasattr(self, 'video') and self.video is not None:
            self.video.release()
            self.video = None
        
    def get_frame(self):
        if self.video is None:
            return None
        success, image = self.video.read()
        if not success:
            return None
        else:
            # Encode frame in JPEG format
            ret, jpeg = cv2.imencode('.jpg', image)
            return jpeg.tobytes()
    
    def get_frame_for_processing(self):
        if self.video is None:
            return None
        success, image = self.video.read()
        if not success:
            return None
        return image

def generate_frames():
    global camera
    if camera is None:
        camera = Camera()
    
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            break

def initialize_app():
    """Initialize the application"""
    global emotion_model
    
    # Create users directory
    os.makedirs(USERS_PATH, exist_ok=True)
    
    # Load emotion model if available
    if EMOTION_MODEL_AVAILABLE and os.path.exists('emotion_model.h5'):
        try:
            emotion_model = load_model('emotion_model.h5', compile=False)
            print("Emotion model loaded successfully")
        except Exception as e:
            print(f"Error loading emotion model: {e}")
            emotion_model = None
    
    # Load registered users
    load_registered_users()
    
    # Load detection history from files
    load_detection_history_from_files()
    
    print("Backend initialized successfully")

def load_registered_users():
    """Load registered users from disk"""
    global registered_users
    
    if not os.path.exists(USERS_PATH):
        return
    
    for user_folder in os.listdir(USERS_PATH):
        user_path = os.path.join(USERS_PATH, user_folder)
        if os.path.isdir(user_path):
            user_image_path = os.path.join(user_path, f"{user_folder}.jpg")
            if os.path.exists(user_image_path):
                try:
                    user_image = fr.load_image_file(user_image_path)
                    # Use multiple encodings for better accuracy
                    user_encodings = fr.face_encodings(user_image, num_jitters=10)
                    if user_encodings:
                        registered_users[user_folder] = {
                            'encoding': user_encodings[0],
                            'image_path': user_image_path,
                            'registration_date': datetime.now().isoformat()
                        }
                        print(f"Loaded user: {user_folder}")
                except Exception as e:
                    print(f"Error loading user {user_folder}: {e}")

def load_detection_history_from_files():
    """Load detection history from report files"""
    global detection_history
    detection_history = []
    
    if not os.path.exists(USERS_PATH):
        return
    
    for user_folder in os.listdir(USERS_PATH):
        user_path = os.path.join(USERS_PATH, user_folder)
        if os.path.isdir(user_path):
            # Load verified user reports
            verified_report_path = os.path.join(user_path, "verified_user_report.txt")
            if os.path.exists(verified_report_path):
                try:
                    with open(verified_report_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Parse the report content
                        for block in content.split('\n\n'):
                            if block.strip():
                                lines = block.strip().split('\n')
                                if len(lines) >= 5:
                                    # Extract info from report format
                                    name_line = lines[0]
                                    similarity_line = lines[4]
                                    motion_line = lines[3] if len(lines) > 3 else "تحرک: 0.0"
                                    
                                    # Extract similarity percentage
                                    similarity = 0
                                    if 'بیشترین شباهت:' in similarity_line:
                                        try:
                                            similarity = float(similarity_line.split(':')[1].replace('%', '').strip())
                                        except:
                                            similarity = 75
                                    
                                    # Extract motion
                                    motion = 0
                                    if 'تحرک:' in motion_line:
                                        try:
                                            motion = float(motion_line.split(':')[1].strip())
                                        except:
                                            motion = 0
                                    
                                    detection_history.append({
                                        'user': user_folder,
                                        'similarity': similarity,
                                        'emotion': 'خنثی',
                                        'motion': motion,
                                        'is_known': True,
                                        'timestamp': datetime.now().isoformat()
                                    })
                except Exception as e:
                    print(f"Error reading verified report for {user_folder}: {e}")
            
            # Load unknown face reports
            unknown_report_path = os.path.join(user_path, "unknown_report.txt")
            if os.path.exists(unknown_report_path):
                try:
                    with open(unknown_report_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                # Parse unknown report format: "ناشناس 20250806_223638 شباهت:45.2% احساس:خنثی تحرک:123.4"
                                parts = line.strip().split()
                                if len(parts) >= 3:
                                    similarity = 45
                                    emotion = 'خنثی'
                                    motion = 0
                                    
                                    for part in parts:
                                        if 'شباهت:' in part:
                                            try:
                                                similarity = float(part.split(':')[1].replace('%', ''))
                                            except:
                                                pass
                                        elif 'احساس:' in part:
                                            emotion = part.split(':')[1]
                                        elif 'تحرک:' in part:
                                            try:
                                                motion = float(part.split(':')[1])
                                            except:
                                                pass
                                    
                                    detection_history.append({
                                        'user': 'ناشناس',
                                        'similarity': similarity,
                                        'emotion': emotion,
                                        'motion': motion,
                                        'is_known': False,
                                        'timestamp': datetime.now().isoformat()
                                    })
                except Exception as e:
                    print(f"Error reading unknown report for {user_folder}: {e}")
    
    print(f"Loaded {len(detection_history)} detection records from files")

def base64_to_image(base64_string):
    """Convert base64 string to OpenCV image"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        pil_image = Image.open(BytesIO(image_data))
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return cv_image
    except Exception as e:
        print(f"Error converting base64 to image: {e}")
        return None

def image_to_base64(image):
    """Convert OpenCV image to base64 string"""
    try:
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{image_base64}"
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def detect_emotion(face_image):
    """Detect emotion from face image"""
    if emotion_model is None:
        # Return random emotion for demo
        return np.random.choice(EMOTION_LABELS)
    
    try:
        # Preprocess face image for emotion detection
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64)) / 255.0
        reshaped = resized.reshape(1, 64, 64, 1)
        
        # Predict emotion
        prediction = emotion_model.predict(reshaped, verbose=0)
        emotion_index = np.argmax(prediction)
        
        return EMOTION_LABELS[emotion_index]
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return "خنثی"

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj

def preprocess_image_for_recognition(image):
    """Preprocess image for better face recognition"""
    # Convert to RGB
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Enhance contrast
    lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
    
    return enhanced

def save_verified_user_report_with_motion(user_name, similarity, emotion, motion):
    """Save verified user report with motion like notebook"""
    try:
        user_folder = os.path.join(USERS_PATH, user_name)
        if not os.path.exists(user_folder):
            return
        
        report_path = os.path.join(user_folder, "verified_user_report.txt")
        
        # Create report content like notebook
        report_content = (
            f"{user_name} در {datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}\n"
            f"مدت حضور: 1.0 ثانیه\n"  
            f"احساس غالب: {emotion}\n"
            f"تحرک: {motion:.1f}\n"
            f"بیشترین شباهت: {similarity:.1f}%\n\n"
        )
        
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"Verified user report saved for {user_name} with motion {motion:.1f}")
        
    except Exception as e:
        print(f"Error saving verified user report: {e}")

def save_unknown_face_report_with_motion(similarity, emotion, face_image, motion):
    """Save unknown face report with motion like notebook"""
    try:
        # Find first user folder to save unknown faces
        if not os.path.exists(USERS_PATH):
            return
        
        user_folders = [f for f in os.listdir(USERS_PATH) if os.path.isdir(os.path.join(USERS_PATH, f))]
        if not user_folders:
            return
        
        user_folder = os.path.join(USERS_PATH, user_folders[0])
        unknown_folder = os.path.join(user_folder, "unknown_faces")
        os.makedirs(unknown_folder, exist_ok=True)
        
        # Save unknown face image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        face_path = os.path.join(unknown_folder, f"unknown_{timestamp}.jpg")
        cv2.imwrite(face_path, face_image)
        
        # Save unknown report
        report_path = os.path.join(user_folder, "unknown_report.txt")
        report_line = f"ناشناس {timestamp} شباهت:{similarity:.1f}% احساس:{emotion} تحرک:{motion:.1f}\n"
        
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(report_line)
        
        print(f"Unknown face report saved with similarity {similarity:.1f}% and motion {motion:.1f}")
        
    except Exception as e:
        print(f"Error saving unknown face report: {e}")

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/register_user', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.get_json()
        user_name = data.get('name', '').strip()
        image_data = data.get('image', '')
        
        if not user_name:
            return jsonify({'success': False, 'message': 'نام کاربر الزامی است'})
        
        if not image_data:
            return jsonify({'success': False, 'message': 'تصویر الزامی است'})
        
        # Convert base64 image to OpenCV format
        image = base64_to_image(image_data)
        if image is None:
            return jsonify({'success': False, 'message': 'خطا در پردازش تصویر'})
        
        # Preprocess image for better recognition
        enhanced_image = preprocess_image_for_recognition(image)
        
        # Detect faces in the image with better model
        face_locations = fr.face_locations(enhanced_image, model='hog')
        
        if len(face_locations) == 0:
            return jsonify({'success': False, 'message': 'هیچ چهره‌ای در تصویر یافت نشد'})
        elif len(face_locations) > 1:
            return jsonify({'success': False, 'message': 'بیش از یک چهره در تصویر یافت شد. لطفاً فقط یک چهره در تصویر باشد'})
        
        # Get face encoding with more samples for better accuracy
        face_encodings = fr.face_encodings(enhanced_image, face_locations, num_jitters=10)
        if not face_encodings:
            return jsonify({'success': False, 'message': 'خطا در استخراج ویژگی‌های چهره'})
        
        # Create user directory
        user_folder = os.path.join(USERS_PATH, user_name)
        os.makedirs(user_folder, exist_ok=True)
        
        # Save user image
        image_path = os.path.join(user_folder, f"{user_name}.jpg")
        cv2.imwrite(image_path, image)
        
        # Store user data
        registered_users[user_name] = {
            'encoding': face_encodings[0],
            'image_path': image_path,
            'registration_date': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True, 
            'message': f'کاربر {user_name} با موفقیت ثبت شد'
        })
        
    except Exception as e:
        print(f"Error registering user: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'خطا در ثبت کاربر'})

@app.route('/api/detect_face', methods=['POST'])
def detect_face():
    """Detect and recognize faces in an image"""
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'تصویر الزامی است'})
        
        # Convert base64 image to OpenCV format
        image = base64_to_image(image_data)
        if image is None:
            return jsonify({'success': False, 'message': 'خطا در پردازش تصویر'})
        
        # Preprocess image for better recognition
        enhanced_image = preprocess_image_for_recognition(image)
        
        # Detect faces with both models for better accuracy
        face_locations_hog = fr.face_locations(enhanced_image, model='hog')
        face_locations_cnn = fr.face_locations(enhanced_image, model='cnn') if len(face_locations_hog) == 0 else []
        
        face_locations = face_locations_hog if len(face_locations_hog) > 0 else face_locations_cnn
        
        if len(face_locations) == 0:
            # Return empty detection if no faces found
            return jsonify({
                'success': True,
                'detections': [],
                'total_faces': 0
            })
        
        # Get face encodings with more jitters for better accuracy
        face_encodings = fr.face_encodings(enhanced_image, face_locations, num_jitters=5)
        
        detections = []
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Extract face image for emotion detection
            if bottom > top and right > left:
                face_image = image[top:bottom, left:right]
                
                # Detect emotion
                emotion = detect_emotion(face_image)
            else:
                emotion = "خنثی"
            
            # Find best match among registered users
            best_match = None
            best_similarity = 0.0
            all_similarities = []
            
            if len(registered_users) > 0:
                for user_name, user_data in registered_users.items():
                    try:
                        # Calculate distance with tolerance
                        distances = fr.face_distance([user_data['encoding']], face_encoding)
                        distance = distances[0]
                        similarity = (1 - float(distance)) * 100
                        all_similarities.append((user_name, similarity))
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = user_name
                            
                    except Exception as e:
                        print(f"Error comparing with user {user_name}: {e}")
                        continue
            
            # Use notebook thresholds - 70% for known, <60% for unknown
            is_known = bool(best_similarity >= 70)
            
            # Calculate motion like notebook
            global user_motion, last_position, user_detected, user_detect_start, start_time, user_emotions
            
            center = ((left + right) // 2, (top + bottom) // 2)
            current_motion = 0
            
            if last_position:
                current_motion = np.linalg.norm(np.array(center) - np.array(last_position))
                user_motion += current_motion
            last_position = center
            
            # Handle user detection state like notebook
            if is_known and best_match:
                if not user_detected:
                    if user_detect_start is None:
                        user_detect_start = time.time()
                        print(f"User {best_match} detection started...")
                    elif time.time() - user_detect_start >= user_activation_time:
                        user_detected = True
                        start_time = time.time()
                        user_motion = 0  # Reset motion when user is confirmed
                        # Initialize emotion tracking
                        user_emotions = {}
                        for e in EMOTION_LABELS:
                            user_emotions[e] = 0
                        print(f"User {best_match} confirmed and system activated.")
                
                # Track emotions when user is detected
                if user_detected:
                    user_emotions[emotion] = user_emotions.get(emotion, 0) + 1
            else:
                # Reset detection state if no known user
                user_detect_start = None
            
            # Debug info
            print(f"Best match: {best_match}, Similarity: {best_similarity:.1f}%, Known: {is_known}, Motion: {current_motion:.1f}")
            if all_similarities:
                print(f"All similarities: {all_similarities}")
            
            detection = {
                'location': {
                    'top': convert_numpy_types(top), 
                    'right': convert_numpy_types(right), 
                    'bottom': convert_numpy_types(bottom), 
                    'left': convert_numpy_types(left)
                },
                'user': str(best_match) if is_known and best_match else 'ناشناس',
                'similarity': convert_numpy_types(round(best_similarity, 1)),
                'emotion': str(emotion),
                'motion': convert_numpy_types(round(current_motion, 1)),
                'total_motion': convert_numpy_types(round(user_motion, 1)),
                'is_known': is_known,
                'timestamp': datetime.now().isoformat()
            }
            
            detections.append(detection)
            
            # Save reports like notebook - only for significant detections
            if is_known and best_match and user_detected:
                # Save verified user report with motion
                save_verified_user_report_with_motion(best_match, best_similarity, emotion, user_motion)
            elif best_similarity < 60 and user_detected:
                # Save unknown face report with motion
                save_unknown_face_report_with_motion(best_similarity, emotion, image[top:bottom, left:right], user_motion)
            
            # Add to detection history (create a copy for history)
            history_detection = detection.copy()
            detection_history.append(history_detection)
            
            # Keep only last 1000 detections
            if len(detection_history) > 1000:
                detection_history.pop(0)
        
        return jsonify({
            'success': True,
            'detections': detections,
            'total_faces': len(detections)
        })
        
    except Exception as e:
        print(f"Error detecting faces: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'خطا در تشخیص چهره'})

@app.route('/api/get_users', methods=['GET'])
def get_users():
    """Get list of registered users"""
    try:
        users = []
        for user_name, user_data in registered_users.items():
            users.append({
                'name': user_name,
                'registration_date': user_data['registration_date']
            })
        
        return jsonify({
            'success': True,
            'users': users,
            'total': len(users)
        })
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'success': False, 'message': 'خطا در دریافت کاربران'})

@app.route('/api/get_detection_history', methods=['GET'])
def get_detection_history():
    """Get detection history"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        user_filter = request.args.get('user', '')
        
        # Filter history
        filtered_history = detection_history
        if user_filter:
            filtered_history = [d for d in detection_history if d['user'] == user_filter]
        
        # Limit results
        recent_history = filtered_history[-limit:] if len(filtered_history) > limit else filtered_history
        recent_history.reverse()  # Most recent first
        
        return jsonify({
            'success': True,
            'history': recent_history,
            'total': len(filtered_history)
        })
        
    except Exception as e:
        print(f"Error getting detection history: {e}")
        return jsonify({'success': False, 'message': 'خطا در دریافت تاریخچه'})

@app.route('/api/get_stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        # Calculate statistics
        total_users = len(registered_users)
        total_detections = len(detection_history)
        
        # Count detections by type
        known_detections = len([d for d in detection_history if d.get('is_known', False)])
        unknown_detections = total_detections - known_detections
        
        # Count emotions
        emotion_counts = {}
        for emotion in EMOTION_LABELS:
            emotion_counts[emotion] = len([d for d in detection_history if d.get('emotion') == emotion])
        
        # Calculate average motion
        total_motion = sum([d.get('motion', 0) for d in detection_history])
        avg_motion = total_motion / total_detections if total_detections > 0 else 0
        
        # Recent activity (last 24 hours)
        recent_time = datetime.now().timestamp() - 24 * 3600
        recent_detections = []
        for d in detection_history:
            try:
                if datetime.fromisoformat(d['timestamp']).timestamp() > recent_time:
                    recent_detections.append(d)
            except:
                continue
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_detections': total_detections,
                'known_detections': known_detections,
                'unknown_detections': unknown_detections,
                'recent_detections': len(recent_detections),
                'average_motion': round(avg_motion, 1),
                'emotion_counts': emotion_counts
            }
        })
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'success': False, 'message': 'خطا در دریافت آمار'})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    """Delete a registered user"""
    try:
        data = request.get_json()
        user_name = data.get('name', '').strip()
        
        if not user_name:
            return jsonify({'success': False, 'message': 'نام کاربر الزامی است'})
        
        if user_name not in registered_users:
            return jsonify({'success': False, 'message': 'کاربر یافت نشد'})
        
        # Remove user data
        user_folder = os.path.join(USERS_PATH, user_name)
        if os.path.exists(user_folder):
            import shutil
            shutil.rmtree(user_folder)
        
        del registered_users[user_name]
        
        return jsonify({
            'success': True,
            'message': f'کاربر {user_name} حذف شد'
        })
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'message': 'خطا در حذف کاربر'})

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    try:
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"Error in video feed: {e}")
        return jsonify({'success': False, 'message': 'خطا در دسترسی به دوربین'})

@app.route('/api/capture_frame', methods=['POST'])
def capture_frame():
    """Capture a single frame from camera"""
    global camera
    try:
        if camera is None:
            camera = Camera()
        
        frame = camera.get_frame_for_processing()
        if frame is None:
            return jsonify({'success': False, 'message': 'خطا در گرفتن عکس از دوربین'})
        
        # Convert frame to base64
        image_base64 = image_to_base64(frame)
        
        return jsonify({
            'success': True,
            'image': image_base64
        })
        
    except Exception as e:
        print(f"Error capturing frame: {e}")
        return jsonify({'success': False, 'message': 'خطا در گرفتن عکس'})

@app.route('/api/check_camera', methods=['GET'])
def check_camera():
    """Check if camera is available"""
    try:
        test_camera = cv2.VideoCapture(0)
        if test_camera.isOpened():
            test_camera.release()
            return jsonify({'success': True, 'message': 'دوربین در دسترس است'})
        else:
            return jsonify({'success': False, 'message': 'دوربین در دسترس نیست'})
    except Exception as e:
        print(f"Error checking camera: {e}")
        return jsonify({'success': False, 'message': 'خطا در بررسی دوربین'})

@app.route('/api/release_camera', methods=['POST'])
def release_camera():
    """Release camera resources"""
    global camera
    try:
        if camera is not None:
            camera.release()
            camera = None
        return jsonify({'success': True, 'message': 'دوربین آزاد شد'})
    except Exception as e:
        print(f"Error releasing camera: {e}")
        return jsonify({'success': False, 'message': 'خطا در آزادسازی دوربین'})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'صفحه یافت نشد'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'خطای داخلی سرور'}), 500

if __name__ == '__main__':
    initialize_app()
    print("Starting Face Recognition Backend...")
    print("Access the web interface at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)