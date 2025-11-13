from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import or_
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash # Required for secure passwords
from PIL import Image
import io
import traceback
import sys

# --- Dynamic Configuration: Render/Vercel URL ---
# RENDER_EXTERNAL_URL is typically provided by Render, otherwise use a default
BASE_URL = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('VERCEL_URL') 
if not BASE_URL:
    # Use a generic placeholder if not running on Render/Vercel
    BASE_URL = 'http://localhost:5000' 

# Import the database models
try:
    from api.database import db, Report, ReportSchema, AdminUser # Ensure AdminUser is imported here
    print("Database models imported successfully")
except ImportError as e:
    print(f"Failed to import database models: {e}")
    print("Make sure database.py is in the same directory")
    sys.exit(1)

# Import your pipeline
try:
    from api.damagepipeline import initialize_pipeline
    print("Pipeline module imported successfully")
except ImportError as e:
    print(f"Pipeline module not found: {e}")
    print("System will work without AI analysis")
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
    print("System will work without budget optimization")
    create_budget_app = None

app = Flask(__name__)

# --- JWT CONFIGURATION AND INITIALIZATION ---
# 1. JWT Secret Key is retrieved from Render/OS Environment Variable
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", 
    "A-Very-Secure-Fallback-Key-For-Local-Use-Only" 
) 
app.config["JWT_TOKEN_LOCATION"] = ["headers"] # Tokens expected in Authorization: Bearer <token> header
jwt = JWTManager(app)
# --- END JWT CONFIG ---

# Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5500", 
            "http://127.0.0.1:5500", 
            "https://roadwatchnigeria.vercel.app",
            "https://www.roadwatchnigeria.site", 
            "https://roadwatchnigeria.site",  
            BASE_URL 
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register budget optimization API
if create_budget_app:
    create_budget_app(app)
    print("Budget optimization endpoints registered")

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Database configuration
DATABASE_URL = os.environ.get('SQLALCHEMY_DATABASE_URI')

if not DATABASE_URL:
    print("Using local SQLite fallback (road_reports.db)")
    DATABASE_URL = 'sqlite:///road_reports.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize pipeline
pipeline = None
if initialize_pipeline:
    try:
        ROAD_CLASSIFIER_PATH = "tomunizua/road-classification_filter"
        TEMP_MODEL_PATH = os.path.join("/tmp", "best.pt")
        pipeline = initialize_pipeline(ROAD_CLASSIFIER_PATH, TEMP_MODEL_PATH)
        
        if pipeline:
            print("Pipeline loaded successfully")
        else:
            print("Pipeline not loaded - check damagepipeline.py logs")
    except Exception as e:
        print(f"Failed to load pipeline: {e}")
        print("System will work without AI analysis")
        pipeline = None
else:
    print("Pipeline module not available")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve uploaded images
@app.route('/api/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve uploaded images"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return jsonify({'error': 'File not found'}), 404

def generate_tracking_number():
    """Generate unique tracking number"""
    return f"RW{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

def save_base64_image(base64_string, filename):
    """Save base64 encoded image to file"""
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
        print(f"Error saving base64 image: {e}")
        return None

# --- ADMIN LOGIN ENDPOINT (SECURE) ---
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        # Query database for user and check password hash
        user = AdminUser.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Create and return JWT token
        access_token = create_access_token(identity=user.username, expires_delta=datetime.timedelta(hours=24))
        return jsonify(token=access_token)
            
    except Exception as e:
        print(f"Database error during login: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server authentication error"}), 500
# --- END ADMIN LOGIN ENDPOINT ---


@app.route('/api/submit-report', methods=['POST', 'OPTIONS'])
def submit_report():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("Report submission started...")
        data = request.get_json()
        
        if not data:
            print("No JSON data received")
            return jsonify({'error': 'No data received'}), 400
        
        print(f"Received data keys: {list(data.keys())}")
        
        required_fields = ['location', 'description', 'lga']
        for field in required_fields:
            if not data.get(field):
                print(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        tracking_number = generate_tracking_number()
        print(f"Generated tracking number: {tracking_number}")
        
        image_filename = None
        damage_detected = False
        damage_type = 'none'
        confidence = 0.0
        severity_score = 0
        estimated_cost = 0
        
        # --- AI/Image Processing Block ---
        if data.get('photo'):
            try:
                print("Processing image...")
                filename = f"{tracking_number}_{secure_filename('report_image.jpg')}"
                image_path = save_base64_image(data['photo'], filename)
                image_filename = filename
                print(f"Image saved temporarily as: {filename}")
                
                if image_path and pipeline:
                    print(f"Running AI analysis on image: {image_path}")
                    analysis_result = pipeline.analyze_image(image_path)
                    
                    if analysis_result['status'] == 'rejected':
                        print(f"Image validation failed: {analysis_result.get('message', 'Not a road image')}")
                        if os.path.exists(image_path):
                            os.remove(image_path)
                            print(f"Deleted temporary file: {filename}")
                        
                        return jsonify({
                            'success': False,
                            'error': 'No road damage image detected',
                            'message': 'The image does not appear to be a road surface. Please upload a clear image of a road with potential damage.',
                            'details': analysis_result.get('message', '')
                        }), 400
                    
                    if analysis_result['status'] == 'completed':
                        summary = analysis_result['summary']
                        damage_detected = summary.get('total_damages', 0) > 0
                        damage_type = summary.get('dominant_damage', 'none') or 'mixed'
                        severity_score = int(summary.get('severity_score', 0) * 100)
                        confidence = 0.95
                        estimated_cost = estimate_repair_cost(damage_type, severity_score, summary.get('total_damages', 0))
                        
                        print(f"AI Analysis complete: {damage_type} damage, severity: {severity_score}")
                    elif analysis_result['status'] == 'no_damage':
                        print(f"Road image validated, but no damage detected")
                        damage_detected = False
                        damage_type = 'none'
                        confidence = 0.95
                        severity_score = 0
                        estimated_cost = 0
                    else:
                        print(f"AI Analysis inconclusive: {analysis_result.get('message', 'Unknown error')}")
                        damage_detected = False
                        damage_type = 'unknown'
                        confidence = 0.5
                else:
                    print("No AI pipeline available for image analysis")
                        
            except Exception as e:
                print(f"Error processing image: {e}")
                traceback.print_exc()
        # --- End AI/Image Processing Block ---
        
        print("Creating database record...")
        
        gps_latitude = None
        gps_longitude = None
        gps_detected = False
        
        if data.get('gps_coordinates'):
            gps_data = data['gps_coordinates']
            gps_latitude = gps_data.get('latitude')
            gps_longitude = gps_data.get('longitude')
            gps_detected = True
            print(f"GPS detected: Lat={gps_latitude}, Lon={gps_longitude}")
        
        new_report = Report(
            tracking_number=tracking_number,
            image_filename=image_filename or '',
            location=data['location'],
            description=data['description'],
            phone=data.get('contact', ''),
            state=data.get('state', 'Lagos'),
            lga=data.get('lga'),
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            gps_detected=gps_detected,
            damage_detected=damage_detected,
            damage_type=damage_type,
            confidence=confidence,
            severity_score=severity_score,
            estimated_cost=estimated_cost,
            status='under_review'
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        print(f"Report created successfully: {tracking_number}")
        
        response = {
            'success': True,
            'tracking_number': tracking_number,
            'message': 'Report submitted successfully',
            'report_id': new_report.id
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error submitting report: {e}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def estimate_repair_cost(damage_type, severity_score, damage_count):
    """Estimate repair cost based on damage type and severity"""
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

@app.route('/api/track/<tracking_number>', methods=['GET'])
def track_report(tracking_number):
    try:
        print(f"Tracking request for: {tracking_number}")
        report = Report.query.filter_by(tracking_number=tracking_number).first()
        
        if not report:
            print(f"Report not found: {tracking_number}")
            return jsonify({'error': 'Report not found'}), 404
        
        print(f"Report found: {tracking_number}")
        
        report_data = {
            'tracking_number': report.tracking_number,
            'location': report.location,
            'status': report.status,
            'state': report.state,
            'lga': report.lga,
            'gps_detected': report.gps_detected,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"Error tracking report: {e}")
        return jsonify({'error': str(e)}), 500

# --- PROTECTED ADMIN ROUTES ---
@app.route('/api/admin/reports', methods=['GET'])
@jwt_required()
def get_admin_reports():
    """Get all reports with AI analysis for admin dashboard"""
    try:
        # Current user identity: get_jwt_identity() 
        print("Admin reports request received")
        reports = Report.query.order_by(Report.created_at.desc()).all()
        print(f"Found {len(reports)} reports")
        
        reports_data = []
        for report in reports:
            photo_url = None
            if report.image_filename:
                filename = secure_filename(report.image_filename)
                photo_url = f"{BASE_URL}/api/uploads/{filename}"
            
            report_dict = {
                'id': report.id,
                'tracking_number': report.tracking_number,
                'location': report.location,
                'description': report.description,
                'phone': report.phone,
                'image_filename': report.image_filename,
                'photo_url': photo_url,
                'state': report.state,
                'lga': report.lga,
                'damage_detected': report.damage_detected,
                'damage_type': report.damage_type,
                'confidence': report.confidence,
                'severity_score': report.severity_score / 100.0,
                'severity_level': get_severity_level(report.severity_score),
                'estimated_cost': report.estimated_cost,
                'status': report.status,
                'created_at': report.created_at.isoformat() if report.created_at else None,
                'updated_at': report.updated_at.isoformat() if report.updated_at else None,
                'ai_analysis': None
            }
            reports_data.append(report_dict)
        
        print(f"Returning {len(reports_data)} reports to admin dashboard")
        return jsonify({'reports': reports_data})
        
    except Exception as e:
        print(f"Error getting admin reports: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/admin/report/<report_id>', methods=['GET'])
@jwt_required()
def get_admin_report_detail(report_id):
    """Get detailed report with full AI analysis for admin"""
    try:
        print(f"Admin report detail request for: {report_id}")
        query_filters = [Report.tracking_number == report_id]
        if report_id.isdigit():
            query_filters.append(Report.id == int(report_id))
        
        report = Report.query.filter(or_(*query_filters)).first()
        
        if not report:
            print(f"Report not found: {report_id}")
            return jsonify({'error': 'Report not found'}), 404
        
        print(f"Report detail found: {report.tracking_number}")
        
        report_data = {
            'id': report.id,
            'tracking_number': report.tracking_number,
            'location': report.location,
            'description': report.description,
            'contact_info': report.phone,
            'phone': report.phone,
            'image_filename': report.image_filename,
            'image_path': f"{BASE_URL}/api/uploads/{report.image_filename}" if report.image_filename else None,
            'damage_detected': report.damage_detected,
            'damage_type': report.damage_type,
            'confidence': report.confidence,
            'severity_score': report.severity_score / 100.0,
            'severity_level': get_severity_level(report.severity_score),
            'estimated_cost': report.estimated_cost,
            'assigned_contractor': report.assigned_contractor,
            'rejection_reason': report.rejection_reason,
            'status': report.status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None,
            'ai_analysis': create_mock_ai_analysis(report)
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"Error getting report detail: {e}")
        return jsonify({'error': str(e)}), 500

def create_mock_ai_analysis(report):
    urgency_map = {
        'high': 'immediate',
        'medium': 'scheduled', 
        'low': 'routine',
        'none': 'monitoring'
    }
    
    severity_level = get_severity_level(report.severity_score)
    
    if not report.damage_detected:
        return {
            'status': 'no_damage',
            'message': 'No road damage detected',
            'summary': {
                'total_damages': 0,
                'damage_types': [],
                'severity_level': 'none',
                'severity_score': 0.0,
                'repair_urgency': 'none'
            },
            'recommendations': ['No immediate action required', 'Continue regular monitoring']
        }
    
    return {
        'status': 'completed',
        'summary': {
            'total_damages': 1 if report.damage_detected else 0,
            'damage_types': [report.damage_type] if report.damage_type and report.damage_type != 'none' else [],
            'severity_level': severity_level,
            'severity_score': report.severity_score / 100.0,
            'repair_urgency': urgency_map.get(severity_level, 'monitoring'),
            'dominant_damage': report.damage_type if report.damage_type != 'none' else None
        },
        'recommendations': generate_recommendations(severity_level, report.damage_type),
        'processing_time': '2.5s'
    }

def generate_recommendations(severity_level, damage_type):
    recommendations = []
    
    if severity_level == 'high':
        recommendations.extend([
            "URGENT: Immediate repair required within 24-48 hours",
            "Consider temporary traffic control measures"
        ])
    elif severity_level == 'medium':
        recommendations.extend([
            "Schedule repair within 2-4 weeks",
            "Monitor for deterioration"
        ])
    elif severity_level == 'low':
        recommendations.extend([
            "Include in routine maintenance cycle",
            "Re-inspect in 3-6 months"
        ])
    else:
        recommendations.append("Continue regular monitoring")
    
    if damage_type == 'pothole':
        recommendations.append("Pothole repair needed - safety priority")
    elif damage_type == 'lateral_crack':
        recommendations.append("Lateral cracks may indicate structural issues")
    elif damage_type == 'longitudinal_crack':
        recommendations.append("Monitor longitudinal crack progression")
    
    return recommendations

@app.route('/api/admin/analytics', methods=['GET'])
@jwt_required()
def get_admin_analytics():
    """Get analytics data for admin dashboard"""
    try:
        print("Admin analytics request received")
        total_reports = Report.query.count()
        completed_reports = Report.query.filter_by(status='completed').count()
        high_severity_reports = Report.query.filter(Report.severity_score >= 70).count()
        
        status_query = db.session.query(Report.status, db.func.count(Report.id)).group_by(Report.status).all()
        status_distribution = dict(status_query)
        
        damage_query = db.session.query(Report.damage_type, db.func.count(Report.id)).group_by(Report.damage_type).all()
        damage_type_distribution = dict(damage_query)
        
        severity_distribution = {
            'low': Report.query.filter(Report.severity_score < 30).count(),
            'medium': Report.query.filter((Report.severity_score >= 30) & (Report.severity_score < 70)).count(),
            'high': Report.query.filter(Report.severity_score >= 70).count()
        }
        
        completion_rate = (completed_reports / total_reports * 100) if total_reports > 0 else 0
        
        analytics_data = {
            'total_reports': total_reports,
            'completed_reports': completed_reports,
            'high_severity_reports': high_severity_reports,
            'completion_rate': round(completion_rate, 1),
            'severity_distribution': severity_distribution,
            'status_distribution': status_distribution,
            'damage_type_distribution': damage_type_distribution
        }
        
        print(f"Analytics data prepared: {total_reports} total reports")
        return jsonify(analytics_data)
        
    except Exception as e:
        print(f"Error getting analytics: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/update-status', methods=['POST'])
@jwt_required()
def update_report_status():
    """Update report status"""
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        new_status = data.get('status')
        assigned_contractor = data.get('assigned_contractor')
        rejection_reason = data.get('rejection_reason')
        
        print(f"Status update request for {report_id} to {new_status}")
        
        if not report_id or not new_status:
            return jsonify({'error': 'Missing report_id or status'}), 400
        
        report = Report.query.filter(
            (Report.id == int(report_id) if report_id.isdigit() else 0) | 
            (Report.tracking_number == report_id)
        ).first()
        
        if not report:
            print(f"Report not found: {report_id}")
            return jsonify({'error': 'Report not found'}), 404
        
        report.status = new_status
        if assigned_contractor:
            report.assigned_contractor = assigned_contractor
        if rejection_reason:
            report.rejection_reason = rejection_reason
        
        db.session.commit()
        
        print(f"Status updated: {report.tracking_number} -> {new_status}")
        return jsonify({'success': True, 'message': 'Status updated successfully'})
        
    except Exception as e:
        print(f"Error updating status: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        total_reports = Report.query.count()
        health_data = {
            'status': 'healthy',
            'pipeline_loaded': pipeline is not None,
            'database_connected': True,
            'total_reports': total_reports,
            'timestamp': datetime.now().isoformat()
        }
        print(f"Health check: {total_reports} reports in database")
        return jsonify(health_data)
    except Exception as e:
        print(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Test endpoint to verify server is running
@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        'message': 'Server is running!',
        'timestamp': datetime.now().isoformat(),
        'base_url': BASE_URL,
        'endpoints': [
            '/api/submit-report',
            '/api/track/<tracking_number>',
            '/api/admin/reports',
            '/api/admin/analytics',
            '/api/health'
        ]
    })

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
            
            # --- INITIAL ADMIN USER CREATION ---
            # NOTE: Use the local script create_initial_admin.py instead of this block for production setup.
            # This block is useful for simple local dev. For production, the AdminUser table must exist.

            report_count = Report.query.count()
            print(f"Current reports in database: {report_count}")

        except Exception as e:
            print(f"Database initialization failed: {e}")
            sys.exit(1)

    port = int(os.environ.get('PORT', 5000))

    print("\n" + "="*60)
    print("Starting RoadWatch Nigeria Backend (Render Deployment)...")
    print(f"Pipeline status: {'Loaded' if pipeline else 'Not loaded'}")
    print(f"Database: PostgreSQL via URL")
    print(f"Live Base URL: {BASE_URL}")
    print(f"Server starting on http://0.0.0.0:{port}")
    print("="*60)

    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)