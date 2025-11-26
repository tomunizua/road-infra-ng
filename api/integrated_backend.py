from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
import uuid
import sys
import threading
import base64
import io
import gc
import cv2
import numpy as np
import math
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image

# --- CONFIGURATION ---
BASE_URL = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('VERCEL_URL') 
if not BASE_URL:
    BASE_URL = 'http://localhost:5000' 

app = Flask(__name__)

# --- JWT CONFIG ---
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "fallback-secret-key") 
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
jwt = JWTManager(app)

# --- CORS CONFIG ---
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://roadwatchnigeria.vercel.app",
            "https://www.roadwatchnigeria.site",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            BASE_URL
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# --- DATABASE CONFIG ---
DATABASE_URL = os.environ.get('SQLALCHEMY_DATABASE_URI')
if not DATABASE_URL:
    print("Using local SQLite fallback")
    DATABASE_URL = 'sqlite:///road_reports.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_size": 10,
    "max_overflow": 20,
}

# --- IMPORT DATABASE MODELS ---
try:
    from database import db, ma, Report, ReportSchema, AdminUser
    print("Database models imported locally")
except ImportError:
    try:
        from api.database import db, ma, Report, ReportSchema, AdminUser
        print("Database models imported from api package")
    except ImportError as e:
        print(f"CRITICAL: Could not import database models: {e}")
        sys.exit(1)

db.init_app(app)
ma.init_app(app)

# --- UPLOAD CONFIG ---
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create tables on startup
with app.app_context():
    try:
        db.create_all()
        print("Database tables initialized")
    except Exception as e:
        print(f"Database warning: {e}")

# --- IMPORT BUDGET API (Same Folder) ---
try:
    from budget_api import create_budget_app
    if create_budget_app:
        create_budget_app(app)
        print("Budget API registered")
except ImportError as e:
    print(f"Budget API skipped: {e}")

# --- GLOBAL PIPELINE VAR ---
pipeline = None 

# --- HELPER FUNCTIONS ---
def get_severity_level(severity_score):
    if severity_score is None: return 'none'
    if severity_score >= 70: return 'high'     
    if severity_score >= 30: return 'medium'    
    if severity_score > 0: return 'low'        
    return 'none'

def get_repair_urgency(severity_level):
    if severity_level == 'high': return 'immediate'
    if severity_level == 'medium': return 'scheduled'
    if severity_level == 'low': return 'routine'
    return 'monitoring'

def estimate_repair_cost(damage_type, severity_score, damage_count):
    if severity_score is None: severity_score = 0
    
    # Realistic Base Costs (₦)
    base_costs = {
        'pothole': 45000,
        'longitudinal_crack': 25000,
        'lateral_crack': 30000,
        'alligator_crack': 85000,
        'mixed': 60000,
        'none': 0
    }
    
    base_cost = base_costs.get(damage_type, 35000)
    severity_multiplier = 1 + (severity_score / 100.0) 
    count_multiplier = max(1, 1 + (damage_count - 1) * 0.5)
    
    total_cost = int(base_cost * severity_multiplier * count_multiplier)
    return ((total_cost + 250) // 500) * 500

def generate_tracking_number():
    return f"RW{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

def save_base64_image(base64_string, filename):
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath, 'JPEG', quality=85)
        return filepath
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

# --- OPENCV DIMENSION ESTIMATION (From model (2).py) ---
def estimate_dimensions_opencv(image_path, user_size_category='Not Specified'):
    """
    Estimates physical dimensions (L, B) in cm using contour analysis and PCA.
    Uses user_size_category to calibrate pixel_per_cm scale.
    """
    try:
        img = cv2.imread(image_path)
        if img is None: return 0, 0
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Otsu's thresholding to find dark spots (potholes)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU)
        
        # Invert if the road is brighter than the pothole (typical)
        # We want the pothole to be white (255) in the mask
        if np.mean(thresh) > 127:
            thresh = cv2.bitwise_not(thresh)
            
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours: return 0, 0
        
        # Find largest contour (assumed to be the main damage)
        cnt = max(contours, key=cv2.contourArea)
        
        # Filter noise
        img_area = img.shape[0] * img.shape[1]
        if cv2.contourArea(cnt) < (0.001 * img_area): return 0, 0 # Too small
        
        # PCA for Major/Minor Axes
        data = cnt.reshape(-1, 2).astype(np.float32)
        mean, eigenvectors = cv2.PCACompute(data, mean=None)
        centered = data - mean
        proj_major = centered @ eigenvectors[0]
        proj_minor = centered @ eigenvectors[1]
        
        length_px = np.max(proj_major) - np.min(proj_major)
        breadth_px = np.max(proj_minor) - np.min(proj_minor)
        
        # --- USER ASSISTED CALIBRATION ---
        # We estimate pixels_per_cm based on what the user said
        target_size_cm = 50.0 # Default
        
        if user_size_category:
            cat = user_size_category.lower()
            if 'small' in cat: target_size_cm = 30.0
            elif 'medium' in cat: target_size_cm = 60.0
            elif 'large' in cat: target_size_cm = 150.0
            
        # Assume the longest dimension detected corresponds to the user's size category
        pixels_per_cm = max(length_px, breadth_px) / target_size_cm
        
        if pixels_per_cm == 0: return 0, 0
        
        length_cm = length_px / pixels_per_cm
        breadth_cm = breadth_px / pixels_per_cm
        
        return round(length_cm, 1), round(breadth_cm, 1)

    except Exception as e:
        print(f"OpenCV Estimation Error: {e}")
        return 0, 0

def classify_severity_from_dimensions(length_cm, breadth_cm):
    """Classify based on physical size (logic from model (2).py)"""
    # Heuristic depth (10% of width)
    depth_cm = min(length_cm, breadth_cm) * 0.1 
    
    if length_cm < 30 and breadth_cm < 20 and depth_cm < 5:
        return 20, "low" # Score 20
    elif length_cm < 60 and depth_cm < 10:
        return 50, "medium" # Score 50
    else:
        return 85, "high" # Score 85

# --- BACKGROUND AI WORKER ---
def process_ai_background(report_id, image_path):
    with app.app_context():
        print(f"[Background] Processing Report {report_id}...")
        try:
            # Lazy import to prevent startup timeout
            print("[Background] Importing AI modules...")
            try:
                from api.damagepipeline import initialize_pipeline
            except ImportError:
                try:
                    from damagepipeline import initialize_pipeline
                except ImportError:
                    print("Could not find pipeline module")
                    return
            
            global pipeline
            if pipeline is None:
                print("[Background] Loading AI Model...")
                possible_paths = [
                    os.path.join("/tmp", "best.pt"),
                    "best.pt",
                    os.path.join(os.getcwd(), "best.pt")
                ]
                TEMP_MODEL_PATH = next((p for p in possible_paths if os.path.exists(p)), os.path.join("/tmp", "best.pt"))
                
                ROAD_CLASSIFIER_PATH = "tomunizua/road-classification_filter"
                pipeline = initialize_pipeline(ROAD_CLASSIFIER_PATH, TEMP_MODEL_PATH)

            if pipeline:
                # 1. Run Roboflow Detection (Finds what it is)
                result = pipeline.analyze_image(image_path)
                
                report = Report.query.get(report_id)
                if report:
                    if result['status'] == 'completed':
                        summary = result['summary']
                        
                        # 2. Run OpenCV Dimension Estimation (Finds how big it is)
                        # Uses user's "Small/Medium/Large" input to calibrate
                        length_cm, breadth_cm = estimate_dimensions_opencv(image_path, report.user_reported_size)
                        
                        # 3. Classify Severity based on Real Dimensions
                        if length_cm > 0:
                            severity_score, severity_level = classify_severity_from_dimensions(length_cm, breadth_cm)
                            print(f"📏 Dimensions: {length_cm}cm x {breadth_cm}cm -> {severity_level}")
                        else:
                            # Fallback if OpenCV fails (too dark/blurry)
                            print("⚠️ OpenCV failed, using fallback severity")
                            severity_score = 50
                            severity_level = "medium"

                        # Update Database
                        report.damage_detected = True
                        report.damage_type = summary.get('dominant_damage', 'none') or 'mixed'
                        report.severity_score = severity_score
                        report.severity_level = severity_level
                        report.repair_urgency = get_repair_urgency(severity_level)
                        report.confidence = 0.95
                        
                        # Cost Estimate using Real Dimensions
                        # We pass the 'length_cm' as a proxy for severity in the cost function
                        # or just stick to score. Let's stick to score to keep it simple.
                        report.estimated_cost = estimate_repair_cost(report.damage_type, severity_score, 1)
                        report.status = 'under_review'
                    
                    elif result['status'] == 'rejected':
                         report.status = 'rejected'
                         report.rejection_reason = "AI Check: Not a road image"
                    
                    elif result['status'] == 'no_damage':
                        report.damage_detected = False
                        report.damage_type = 'none'
                        report.severity_score = 0
                        report.severity_level = 'none'
                        report.status = 'completed'

                    db.session.commit()
                    print(f"✅ [Background] Report {report_id} updated.")
            
            gc.collect()
            
        except Exception as e:
            print(f"Background Error: {e}")
            import traceback
            traceback.print_exc()

# --- ROUTES ---

@app.route('/api/submit-report', methods=['POST'])
def submit_report():
    try:
        data = request.get_json()
        if not data: return jsonify({'error': 'No data'}), 400
        
        tracking_number = generate_tracking_number()
        image_filename = None
        image_path = None
        
        if data.get('photo'):
            filename = f"{tracking_number}_{secure_filename('report.jpg')}"
            image_path = save_base64_image(data['photo'], filename)
            image_filename = filename

        gps_data = data.get('gps_coordinates', {})
        reported_size = data.get('size', 'Not Specified')

        new_report = Report(
            tracking_number=tracking_number,
            image_filename=image_filename or '',
            location=data.get('location', 'Unknown'),
            description=data.get('description', ''),
            phone=data.get('contact', ''),
            user_reported_size=reported_size,
            state=data.get('state', 'Lagos'),
            lga=data.get('lga'),
            gps_latitude=gps_data.get('lat'),
            gps_longitude=gps_data.get('lng'),
            gps_detected=bool(gps_data),
            status='submitted',
            damage_type='processing'
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        if image_filename and image_path:
            thread = threading.Thread(target=process_ai_background, args=(new_report.id, image_path))
            thread.start()
        
        return jsonify({
            'success': True,
            'tracking_number': tracking_number,
            'message': 'Report submitted! AI analysis in progress.',
            'report_id': new_report.id
        })
        
    except Exception as e:
        print(f"Error submitting report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    try:
        user = AdminUser.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        access_token = create_access_token(identity=user.username)
        return jsonify(token=access_token)
    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({"error": "Server error"}), 500

@app.route('/api/admin/reports', methods=['GET'])
@jwt_required()
def get_admin_reports():
    try:
        reports = Report.query.order_by(Report.created_at.desc()).all()
        reports_data = []
        for r in reports:
            photo_url = None
            if r.image_filename:
                photo_url = f"{BASE_URL}/api/uploads/{secure_filename(r.image_filename)}"
            
            reports_data.append({
                'id': r.id,
                'tracking_number': r.tracking_number,
                'location': r.location,
                'description': r.description,
                'damage_type': r.damage_type or 'processing',
                'severity_score': (r.severity_score or 0) / 100.0,
                'severity_level': r.severity_level,
                'repair_urgency': r.repair_urgency,
                'user_reported_size': r.user_reported_size,
                'status': r.status,
                'estimated_cost': r.estimated_cost or 0,
                'photo_url': photo_url,
                'created_at': r.created_at.isoformat(),
                'lga': r.lga,
                'confidence': r.confidence or 0.0
            })
        return jsonify({'reports': reports_data})
    except Exception as e:
        print(f"Admin Report List Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reprocess/<int:report_id>', methods=['POST'])
@jwt_required()
def force_reprocess(report_id):
    try:
        report = Report.query.get(report_id)
        if not report: return jsonify({'error': 'Report not found'}), 404
        if not report.image_filename: return jsonify({'error': 'No image'}), 400

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], report.image_filename)
        thread = threading.Thread(target=process_ai_background, args=(report.id, image_path))
        thread.start()
        
        return jsonify({'message': f'Reprocessing triggered for {report.tracking_number}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-admin', methods=['GET'])
def create_initial_admin():
    try:
        if AdminUser.query.filter_by(username='admin').first():
            return jsonify({'message': 'Admin already exists'}), 200
        admin = AdminUser(username='admin')
        admin.set_password('roadwatch2025') 
        db.session.add(admin)
        db.session.commit()
        return jsonify({'message': 'Admin created: admin / roadwatch2025'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/track/<tracking_number>', methods=['GET'])
def track_report(tracking_number):
    try:
        report = Report.query.filter_by(tracking_number=tracking_number).first()
        if not report: return jsonify({'error': 'Not found'}), 404
        return jsonify({
            'tracking_number': report.tracking_number,
            'status': report.status,
            'damage_type': report.damage_type,
            'severity_level': report.severity_level,
            'estimated_cost': report.estimated_cost,
            'location': report.location,
            'created_at': report.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        total = Report.query.count()
        return jsonify({'status': 'healthy', 'total_reports': total, 'pipeline_active': pipeline is not None})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)