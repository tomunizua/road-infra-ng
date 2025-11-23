from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import or_
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import io
import traceback
import sys
import threading
import base64
import gc

# --- Dynamic Configuration: Render/Vercel URL ---
BASE_URL = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('VERCEL_URL') 
if not BASE_URL:
    BASE_URL = 'http://localhost:5000' 

# Import the database models
try:
    from api.database import db, Report, ReportSchema, AdminUser
    print("Database models imported successfully")
except ImportError as e:
    print(f"Failed to import database models: {e}")
    sys.exit(1)

# Import your pipeline (But don't load it yet)
try:
    from api.damagepipeline import initialize_pipeline
    print("Pipeline module imported successfully")
except ImportError as e:
    print(f"Pipeline module not found: {e}")
    initialize_pipeline = None

# Import budget optimization API
try:
    budget_dir = os.path.join(os.path.dirname(__file__), '..', 'budget_optimization')
    if budget_dir not in sys.path:
        sys.path.insert(0, budget_dir)
    from budget_api import create_budget_app
    print("Budget optimization API imported successfully")
except ImportError as e:
    print(f"Budget optimization not found: {e}")
    create_budget_app = None

app = Flask(__name__)

# --- JWT CONFIGURATION ---
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "fallback-secret-key") 
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
jwt = JWTManager(app)

# --- CORS CONFIGURATION ---
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

# Register budget app
if create_budget_app:
    create_budget_app(app)

# App Configuration
UPLOAD_FOLDER = '/tmp/uploads' # Use /tmp for Render
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Database Configuration
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

db.init_app(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create tables on startup
with app.app_context():
    try:
        db.create_all()
        print("Database tables initialized")
    except Exception as e:
        print(f"Database warning: {e}")

# --- CRITICAL: GLOBAL PIPELINE VARIABLE (START AS NONE) ---
# We do NOT load the AI model here. It loads lazily in the background thread.
pipeline = None 

# --- HELPER FUNCTIONS ---
def estimate_repair_cost(damage_type, severity_score, damage_count):
    """Estimate repair cost"""
    base_costs = {
        'pothole': 500,
        'longitudinal_crack': 200,
        'lateral_crack': 300,
        'mixed': 400,
        'none': 0,
        'unknown': 250
    }
    base_cost = base_costs.get(damage_type, 250)
    severity_multiplier = 1 + (severity_score / 100) * 2
    count_multiplier = max(1, damage_count * 0.8)
    total_cost = int(base_cost * severity_multiplier * count_multiplier)
    return ((total_cost + 25) // 50) * 50

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

def get_severity_level(severity_score):
    """Convert severity score (0-100) to level"""
    if severity_score >= 70:
        return 'high'
    elif severity_score >= 30:
        return 'medium'
    elif severity_score > 0:
        return 'low'
    else:
        return 'none'

def generate_recommendations(severity_level, damage_type):
    recommendations = []
    if severity_level == 'high':
        recommendations.extend(["URGENT: Immediate repair required", "Consider traffic control"])
    elif severity_level == 'medium':
        recommendations.extend(["Schedule repair within 2-4 weeks", "Monitor for deterioration"])
    elif severity_level == 'low':
        recommendations.extend(["Include in routine maintenance", "Re-inspect in 3-6 months"])
    else:
        recommendations.append("Continue regular monitoring")
    return recommendations

# --- BACKGROUND AI WORKER ---
def process_ai_background(report_id, image_path):
    """Runs in background to prevent server timeout"""
    with app.app_context():
        print(f"[Background] Processing Report {report_id}...")
        try:
            # 1. Lazy Load Pipeline (Only if needed)
            global pipeline
            if pipeline is None and initialize_pipeline:
                print("[Background] Loading AI Model into RAM...")
                ROAD_CLASSIFIER_PATH = "tomunizua/road-classification_filter"
                TEMP_MODEL_PATH = os.path.join("/tmp", "best.pt")
                pipeline = initialize_pipeline(ROAD_CLASSIFIER_PATH, TEMP_MODEL_PATH)

            # 2. Run Analysis
            if pipeline:
                result = pipeline.analyze_image(image_path)
                
                # 3. Update Database
                report = Report.query.get(report_id)
                if report:
                    if result['status'] == 'completed':
                        summary = result['summary']
                        report.damage_detected = summary.get('total_damages', 0) > 0
                        report.damage_type = summary.get('dominant_damage', 'none') or 'mixed'
                        report.severity_score = int(summary.get('severity_score', 0) * 100)
                        report.confidence = 0.95
                        report.estimated_cost = estimate_repair_cost(report.damage_type, report.severity_score, summary.get('total_damages', 0))
                        report.status = 'under_review'
                    elif result['status'] == 'rejected':
                         report.status = 'rejected'
                         report.rejection_reason = "AI Check: Not a road image"
                    
                    db.session.commit()
                    print(f"[Background] Report {report_id} analysis finished.")
            
            # 4. Cleanup Memory immediately
            gc.collect()
            
        except Exception as e:
            print(f"[Background] Error: {e}")

# --- API ROUTES ---

@app.route('/api/submit-report', methods=['POST'])
def submit_report():
    try:
        data = request.get_json()
        if not data: return jsonify({'error': 'No data'}), 400
        
        # 1. Generate ID and Save Image
        tracking_number = generate_tracking_number()
        image_filename = None
        image_path = None
        
        if data.get('photo'):
            filename = f"{tracking_number}_{secure_filename('report.jpg')}"
            image_path = save_base64_image(data['photo'], filename)
            image_filename = filename

        # 2. Create Database Record IMMEDIATELY (Status: submitted/processing)
        gps_data = data.get('gps_coordinates', {})
        
        new_report = Report(
            tracking_number=tracking_number,
            image_filename=image_filename or '',
            location=data.get('location', 'Unknown'),
            description=data.get('description', ''),
            phone=data.get('contact', ''),
            state=data.get('state', 'Lagos'),
            lga=data.get('lga'),
            gps_latitude=gps_data.get('latitude'),
            gps_longitude=gps_data.get('longitude'),
            gps_detected=bool(gps_data),
            damage_detected=False, # Will be updated by AI later
            damage_type='processing', # Visual cue for user
            confidence=0.0,
            severity_score=0,
            estimated_cost=0,
            status='submitted'
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        # 3. Trigger Background AI (Fire and Forget)
        if image_filename and image_path:
            thread = threading.Thread(target=process_ai_background, args=(new_report.id, image_path))
            thread.start()
        
        # 4. Return Success Instantly
        print(f"Report {tracking_number} submitted. AI running in background.")
        return jsonify({
            'success': True,
            'tracking_number': tracking_number,
            'message': 'Report submitted! AI analysis in progress.',
            'report_id': new_report.id,
            'ai_analysis': {
                'damage_type': 'Analyzing...',
                'confidence': 'Pending'
            }
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

# --- TEMPORARY ROUTE TO CREATE ADMIN ---
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
            'estimated_cost': report.estimated_cost,
            'location': report.location,
            'created_at': report.created_at.isoformat() if report.created_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reports', methods=['GET'])
@jwt_required()
def get_admin_reports():
    try:
        reports = Report.query.order_by(Report.created_at.desc()).all()
        reports_data = []
        for r in reports:
            photo_url = f"{BASE_URL}/api/uploads/{secure_filename(r.image_filename)}" if r.image_filename else None
            reports_data.append({
                'id': r.id,
                'tracking_number': r.tracking_number,
                'location': r.location,
                'damage_type': r.damage_type,
                'severity_score': r.severity_score / 100.0,
                'status': r.status,
                'estimated_cost': r.estimated_cost,
                'photo_url': photo_url,
                'created_at': r.created_at.isoformat(),
                'lga': r.lga
            })
        return jsonify({'reports': reports_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file: {e}")
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        total_reports = Report.query.count()
        return jsonify({
            'status': 'healthy',
            'database_connected': True,
            'total_reports': total_reports,
            'pipeline_active': pipeline is not None
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({'message': 'Server is running', 'base_url': BASE_URL})

# --- FORCE CORS ON ERRORS ---
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in [
        "https://roadwatchnigeria.vercel.app",
        "https://www.roadwatchnigeria.site",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        BASE_URL
    ]:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)