from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import or_
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
from PIL import Image
import io
import traceback

# Import the database models
try:
    from database import db, Report, ReportSchema
    print("✅ Database models imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database models: {e}")
    print("   Make sure database.py is in the same directory")
    exit(1)

# Import your pipeline
try:
    from damagepipeline import initialize_pipeline
    print("✅ Pipeline module imported successfully")
except ImportError as e:
    print(f"⚠️  Pipeline module not found: {e}")
    print("   System will work without AI analysis")
    initialize_pipeline = None

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:5000", "http://127.0.0.1:5000", "file://"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///road_reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize pipeline
pipeline = None
if initialize_pipeline:
    try:
        # Update these paths for your actual models
        ROAD_CLASSIFIER_PATH = "tomunizua/road-classification_filter"
        
        # Use proper path resolution for YOLO model
        YOLO_MODEL_PATH = "models/best.pt"  # UPDATE THIS PATH
        
        # Verify the model file exists
        if not os.path.exists(YOLO_MODEL_PATH):
            print(f"⚠️  YOLO model not found at: {YOLO_MODEL_PATH}")
            print("   Please check the path or copy the model to the correct location")
            YOLO_MODEL_PATH = None
        
        if YOLO_MODEL_PATH:
            pipeline = initialize_pipeline(ROAD_CLASSIFIER_PATH, YOLO_MODEL_PATH)
            print("✅ Pipeline loaded successfully")
        else:
            print("⚠️  Pipeline not loaded - YOLO model path issue")
    except Exception as e:
        print(f"❌ Failed to load pipeline: {e}")
        print("   System will work without AI analysis")
        pipeline = None
else:
    print("⚠️  Pipeline module not available")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_tracking_number():
    """Generate unique tracking number"""
    return f"RW{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

def save_base64_image(base64_string, filename):
    """Save base64 encoded image to file"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Open and save image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Save image
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath, 'JPEG', quality=85)
        
        return filepath
    except Exception as e:
        print(f"Error saving base64 image: {e}")
        return None

@app.route('/api/submit-report', methods=['POST', 'OPTIONS'])
def submit_report():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        print("📝 Report submission started...")
        data = request.get_json()
        
        if not data:
            print("❌ No JSON data received")
            return jsonify({'error': 'No data received'}), 400
        
        print(f"📊 Received data keys: {list(data.keys())}")
        
        # Validate required fields
        required_fields = ['location', 'description']
        for field in required_fields:
            if not data.get(field):
                print(f"❌ Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate tracking number
        tracking_number = generate_tracking_number()
        print(f"🎫 Generated tracking number: {tracking_number}")
        
        # Handle image data
        image_filename = None
        ai_analysis = None
        damage_detected = False
        damage_type = 'none'
        confidence = 0.0
        severity_score = 0
        estimated_cost = 0
        
        if data.get('photo'):
            try:
                print("📷 Processing image...")
                # Save uploaded image
                filename = f"{tracking_number}_{secure_filename('report_image.jpg')}"
                image_path = save_base64_image(data['photo'], filename)
                image_filename = filename
                print(f"💾 Image saved as: {filename}")
                
                if image_path and pipeline:
                    print(f"🤖 Running AI analysis on image: {image_path}")
                    
                    # Run your pipeline analysis
                    analysis_result = pipeline.analyze_image(image_path)
                    
                    if analysis_result['status'] == 'completed':
                        summary = analysis_result['summary']
                        damage_detected = summary.get('total_damages', 0) > 0
                        damage_type = summary.get('dominant_damage', 'none') or 'mixed'
                        severity_score = int(summary.get('severity_score', 0) * 100)  # Convert to 0-100 scale
                        confidence = 0.95  # High confidence if pipeline completed
                        
                        # Simple cost estimation based on severity and damage type
                        estimated_cost = estimate_repair_cost(damage_type, severity_score, summary.get('total_damages', 0))
                        
                        # Store AI analysis for admin dashboard
                        ai_analysis = json.dumps(analysis_result)
                        
                        print(f"✅ AI Analysis complete: {damage_type} damage, severity: {severity_score}")
                    else:
                        print(f"⚠️  AI Analysis failed: {analysis_result.get('message', 'Unknown error')}")
                        damage_detected = False
                        damage_type = 'unknown'
                        confidence = 0.5
                        ai_analysis = json.dumps(analysis_result)
                else:
                    print("⚠️  No AI pipeline available for image analysis")
                        
            except Exception as e:
                print(f"❌ Error processing image: {e}")
                traceback.print_exc()
        
        # Create new report using SQLAlchemy model
        print("💾 Creating database record...")
        new_report = Report(
            tracking_number=tracking_number,
            image_filename=image_filename or '',
            location=data['location'],
            description=data['description'],
            phone=data.get('contact', ''),
            damage_detected=damage_detected,
            damage_type=damage_type,
            confidence=confidence,
            severity_score=severity_score,
            estimated_cost=estimated_cost,
            status='under_review'
        )
        
        # Save to database
        db.session.add(new_report)
        db.session.commit()
        
        print(f"✅ Report created successfully: {tracking_number}")
        
        # Prepare response (NO AI analysis shown to public)
        response = {
            'success': True,
            'tracking_number': tracking_number,
            'message': 'Report submitted successfully',
            'report_id': new_report.id
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error submitting report: {e}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def estimate_repair_cost(damage_type, severity_score, damage_count):
    """Estimate repair cost based on damage type and severity"""
    base_costs = {
        'pothole': 500,  # NGN per pothole
        'longitudinal_crack': 200,  # NGN per meter
        'lateral_crack': 300,  # NGN per meter
        'mixed': 400,
        'none': 0,
        'unknown': 250
    }
    
    base_cost = base_costs.get(damage_type, 250)
    
    # Scale by severity (0-100)
    severity_multiplier = 1 + (severity_score / 100) * 2  # 1x to 3x multiplier
    
    # Scale by damage count
    count_multiplier = max(1, damage_count * 0.8)  # Slight efficiency for multiple damages
    
    total_cost = int(base_cost * severity_multiplier * count_multiplier)
    
    # Round to nearest 50 NGN
    return ((total_cost + 25) // 50) * 50

@app.route('/api/track/<tracking_number>', methods=['GET'])
def track_report(tracking_number):
    try:
        print(f"🔍 Tracking request for: {tracking_number}")
        # Query using SQLAlchemy
        report = Report.query.filter_by(tracking_number=tracking_number).first()
        
        if not report:
            print(f"❌ Report not found: {tracking_number}")
            return jsonify({'error': 'Report not found'}), 404
        
        print(f"✅ Report found: {tracking_number}")
        
        # Return basic info only (NO AI analysis for public)
        report_data = {
            'tracking_number': report.tracking_number,
            'location': report.location,
            'status': report.status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"❌ Error tracking report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reports', methods=['GET'])
def get_admin_reports():
    """Get all reports with AI analysis for admin dashboard"""
    try:
        print("📊 Admin reports request received")
        # Query all reports using SQLAlchemy
        reports = Report.query.order_by(Report.created_at.desc()).all()
        print(f"📋 Found {len(reports)} reports")
        
        # Convert to dictionaries with admin-specific formatting
        reports_data = []
        for report in reports:
            report_dict = {
                'id': report.id,
                'tracking_number': report.tracking_number,
                'location': report.location,
                'description': report.description,
                'phone': report.phone,
                'image_filename': report.image_filename,
                'damage_detected': report.damage_detected,
                'damage_type': report.damage_type,
                'damage_types': [report.damage_type] if report.damage_type and report.damage_type != 'none' else [],
                'confidence': report.confidence,
                'severity_score': report.severity_score / 100.0,  # Convert back to 0-1 scale for consistency
                'severity_level': get_severity_level(report.severity_score),
                'estimated_cost': report.estimated_cost,
                'assigned_contractor': report.assigned_contractor,
                'rejection_reason': report.rejection_reason,
                'status': report.status,
                'created_at': report.created_at.isoformat() if report.created_at else None,
                'updated_at': report.updated_at.isoformat() if report.updated_at else None,
                'ai_analysis': None  # Will be populated if needed
            }
            reports_data.append(report_dict)
        
        print(f"✅ Returning {len(reports_data)} reports to admin dashboard")
        return jsonify({'reports': reports_data})
        
    except Exception as e:
        print(f"❌ Error getting admin reports: {e}")
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
def get_admin_report_detail(report_id):
    """Get detailed report with full AI analysis for admin"""
    try:
        print(f"📝 Admin report detail request for: {report_id}")
        # Query by ID or tracking number
        query_filters = [Report.tracking_number == report_id]
        if report_id.isdigit():
            query_filters.append(Report.id == int(report_id))
        
        report = Report.query.filter(or_(*query_filters)).first()
        
        if not report:
            print(f"❌ Report not found: {report_id}")
            return jsonify({'error': 'Report not found'}), 404
        
        print(f"✅ Report detail found: {report.tracking_number}")
        
        # Return full report data with admin formatting
        report_data = {
            'id': report.id,
            'tracking_number': report.tracking_number,
            'location': report.location,
            'description': report.description,
            'contact_info': report.phone,  # Admin dashboard expects contact_info
            'phone': report.phone,
            'image_filename': report.image_filename,
            'image_path': f"/uploads/{report.image_filename}" if report.image_filename else None,
            'damage_detected': report.damage_detected,
            'damage_type': report.damage_type,
            'damage_types': [report.damage_type] if report.damage_type and report.damage_type != 'none' else [],
            'confidence': report.confidence,
            'severity_score': report.severity_score / 100.0,  # Convert back to 0-1 scale
            'severity_level': get_severity_level(report.severity_score),
            'estimated_cost': report.estimated_cost,
            'assigned_contractor': report.assigned_contractor,
            'rejection_reason': report.rejection_reason,
            'status': report.status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None,
            'ai_analysis': create_mock_ai_analysis(report)  # Create mock AI analysis structure
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"❌ Error getting report detail: {e}")
        return jsonify({'error': str(e)}), 500

def create_mock_ai_analysis(report):
    """Create mock AI analysis structure for admin dashboard compatibility"""
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
    
    # Create realistic analysis structure
    urgency_map = {
        'high': 'immediate',
        'medium': 'scheduled', 
        'low': 'routine',
        'none': 'monitoring'
    }
    
    severity_level = get_severity_level(report.severity_score)
    
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
    """Generate recommendations based on severity and damage type"""
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
    
    # Damage-specific recommendations
    if damage_type == 'pothole':
        recommendations.append("Pothole repair needed - safety priority")
    elif damage_type == 'lateral_crack':
        recommendations.append("Lateral cracks may indicate structural issues")
    elif damage_type == 'longitudinal_crack':
        recommendations.append("Monitor longitudinal crack progression")
    
    return recommendations

@app.route('/api/admin/analytics', methods=['GET'])
def get_admin_analytics():
    """Get analytics data for admin dashboard"""
    try:
        print("📈 Admin analytics request received")
        # Get basic stats using SQLAlchemy
        total_reports = Report.query.count()
        completed_reports = Report.query.filter_by(status='completed').count()
        high_severity_reports = Report.query.filter(Report.severity_score >= 70).count()
        
        # Status distribution
        status_query = db.session.query(Report.status, db.func.count(Report.id)).group_by(Report.status).all()
        status_distribution = dict(status_query)
        
        # Damage type distribution
        damage_query = db.session.query(Report.damage_type, db.func.count(Report.id)).group_by(Report.damage_type).all()
        damage_type_distribution = dict(damage_query)
        
        # Severity distribution
        severity_distribution = {
            'low': Report.query.filter(Report.severity_score < 30).count(),
            'medium': Report.query.filter((Report.severity_score >= 30) & (Report.severity_score < 70)).count(),
            'high': Report.query.filter(Report.severity_score >= 70).count()
        }
        
        # Calculate metrics
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
        
        print(f"✅ Analytics data prepared: {total_reports} total reports")
        return jsonify(analytics_data)
        
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/update-status', methods=['POST'])
def update_report_status():
    """Update report status"""
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        new_status = data.get('status')
        assigned_contractor = data.get('assigned_contractor')
        rejection_reason = data.get('rejection_reason')
        
        print(f"🔄 Status update request for {report_id} to {new_status}")
        
        if not report_id or not new_status:
            return jsonify({'error': 'Missing report_id or status'}), 400
        
        # Find report
        report = Report.query.filter(
            (Report.id == int(report_id) if report_id.isdigit() else 0) | 
            (Report.tracking_number == report_id)
        ).first()
        
        if not report:
            print(f"❌ Report not found: {report_id}")
            return jsonify({'error': 'Report not found'}), 404
        
        # Update fields
        report.status = new_status
        if assigned_contractor:
            report.assigned_contractor = assigned_contractor
        if rejection_reason:
            report.rejection_reason = rejection_reason
        
        # Save changes
        db.session.commit()
        
        print(f"✅ Status updated: {report.tracking_number} -> {new_status}")
        return jsonify({'success': True, 'message': 'Status updated successfully'})
        
    except Exception as e:
        print(f"❌ Error updating status: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        total_reports = Report.query.count()
        health_data = {
            'status': 'healthy',
            'pipeline_loaded': pipeline is not None,
            'database_connected': True,
            'total_reports': total_reports,
            'timestamp': datetime.now().isoformat()
        }
        print(f"💚 Health check: {total_reports} reports in database")
        return jsonify(health_data)
    except Exception as e:
        print(f"❌ Health check failed: {e}")
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
        'endpoints': [
            '/api/submit-report',
            '/api/track/<tracking_number>',
            '/api/admin/reports',
            '/api/admin/analytics',
            '/api/health'
        ]
    })

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'redo.html')

@app.route('/<filename>')
def serve_static(filename):
    if filename.endswith('.html'):
        return send_from_directory('.', filename)
    return "File not found", 404

if __name__ == '__main__':
    with app.app_context():
        try:
            # Create all database tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if we have any data
            report_count = Report.query.count()
            print(f"📊 Current reports in database: {report_count}")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            exit(1)
    
    print("\n" + "="*60)
    print("🚀 Starting RoadWatch Nigeria Backend...")
    print(f"🤖 Pipeline status: {'✅ Loaded' if pipeline else '⚠️ Not loaded'}")
    print(f"🗄️  Database: SQLAlchemy with SQLite")
    print(f"🌐 Server starting on http://localhost:5000")
    print(f"📋 Test endpoint: http://localhost:5000/api/test")
    print(f"💚 Health check: http://localhost:5000/api/health")
    print(f"👥 Citizen Portal: http://localhost:5000/redo.html")
    print(f"📊 Admin Dashboard: http://localhost:5000/admin.html")
    print("="*60)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)