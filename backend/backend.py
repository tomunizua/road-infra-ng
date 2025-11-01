from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
import sqlite3
from werkzeug.utils import secure_filename
import base64
from PIL import Image
import io
import traceback

# Import your pipeline
try:
    from road_damage_pipeline import initialize_pipeline
    print("Pipeline module imported successfully")
except ImportError as e:
    print(f"Failed to import pipeline: {e}")
    initialize_pipeline = None

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('road_reports.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            tracking_number TEXT UNIQUE NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            contact_info TEXT,
            image_path TEXT,
            gps_coordinates TEXT,
            ai_analysis TEXT,
            damage_types TEXT,
            severity_level TEXT,
            severity_score REAL,
            repair_urgency TEXT,
            status TEXT DEFAULT 'submitted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize pipeline
pipeline = None
if initialize_pipeline:
    try:
        # Update these paths for your actual models
        ROAD_CLASSIFIER_PATH = "tomunizua/road-classification_filter"
        YOLO_MODEL_PATH = "path/to/your/best.pt"  # UPDATE THIS PATH
        
        pipeline = initialize_pipeline(ROAD_CLASSIFIER_PATH, YOLO_MODEL_PATH)
        print("Pipeline loaded successfully")
    except Exception as e:
        print(f"Failed to load pipeline: {e}")
        pipeline = None
else:
    print("Pipeline module not available")

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

@app.route('/api/submit-report', methods=['POST'])
def submit_report():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['location', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate tracking number
        tracking_number = generate_tracking_number()
        report_id = str(uuid.uuid4())
        
        # Handle image data
        image_path = None
        ai_analysis = None
        damage_types = []
        severity_level = 'unknown'
        severity_score = 0.0
        repair_urgency = 'pending'
        
        if data.get('photo'):
            try:
                # Save uploaded image
                filename = f"{report_id}_{secure_filename('report_image.jpg')}"
                image_path = save_base64_image(data['photo'], filename)
                
                if image_path and pipeline:
                    print(f"Running AI analysis on image: {image_path}")
                    
                    # Run your pipeline analysis
                    analysis_result = pipeline.analyze_image(image_path)
                    
                    if analysis_result['status'] == 'completed':
                        summary = analysis_result['summary']
                        severity_level = summary.get('severity_level', 'unknown')
                        severity_score = summary.get('severity_score', 0.0)
                        repair_urgency = summary.get('repair_urgency', 'pending')
                        damage_types = summary.get('damage_types', [])
                        
                        # Store full analysis for admin dashboard
                        ai_analysis = json.dumps(analysis_result)
                        
                        print(f"AI Analysis complete: {severity_level} severity, score: {severity_score}")
                    else:
                        print(f"AI Analysis failed: {analysis_result.get('message', 'Unknown error')}")
                        ai_analysis = json.dumps(analysis_result)
                        
            except Exception as e:
                print(f"Error processing image: {e}")
                traceback.print_exc()
        
        # Store in database
        conn = sqlite3.connect('road_reports.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reports (
                id, tracking_number, location, description, contact_info, 
                image_path, gps_coordinates, ai_analysis, damage_types,
                severity_level, severity_score, repair_urgency, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id, tracking_number, data['location'], data['description'],
            data.get('contact', ''), image_path, data.get('gps', ''),
            ai_analysis, json.dumps(damage_types), severity_level, 
            severity_score, repair_urgency, 'submitted'
        ))
        
        conn.commit()
        conn.close()
        
        # Prepare response (NO AI analysis shown to public)
        response = {
            'success': True,
            'tracking_number': tracking_number,
            'message': 'Report submitted successfully'
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error submitting report: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/track/<tracking_number>', methods=['GET'])
def track_report(tracking_number):
    try:
        conn = sqlite3.connect('road_reports.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tracking_number, location, status, created_at, updated_at 
            FROM reports WHERE tracking_number = ?
        ''', (tracking_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Report not found'}), 404
        
        # Return basic info only (NO AI analysis for public)
        report_data = {
            'tracking_number': row[0],
            'location': row[1],
            'status': row[2],
            'created_at': row[3],
            'updated_at': row[4]
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"Error tracking report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reports', methods=['GET'])
def get_admin_reports():
    """Get all reports with AI analysis for admin dashboard"""
    try:
        conn = sqlite3.connect('road_reports.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, tracking_number, location, description, damage_types,
                   severity_level, severity_score, repair_urgency, status, 
                   created_at, ai_analysis
            FROM reports
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'tracking_number', 'location', 'description', 'damage_types',
                  'severity_level', 'severity_score', 'repair_urgency', 'status', 
                  'created_at', 'ai_analysis']
        
        reports = []
        for row in rows:
            report = dict(zip(columns, row))
            
            # Parse JSON fields
            try:
                if report['damage_types']:
                    report['damage_types'] = json.loads(report['damage_types'])
                else:
                    report['damage_types'] = []
            except:
                report['damage_types'] = []
            
            try:
                if report['ai_analysis']:
                    report['ai_analysis'] = json.loads(report['ai_analysis'])
            except:
                report['ai_analysis'] = None
            
            reports.append(report)
        
        return jsonify({'reports': reports})
        
    except Exception as e:
        print(f"Error getting admin reports: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/report/<report_id>', methods=['GET'])
def get_admin_report_detail(report_id):
    """Get detailed report with full AI analysis for admin"""
    try:
        conn = sqlite3.connect('road_reports.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM reports WHERE id = ? OR tracking_number = ?
        ''', (report_id, report_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Report not found'}), 404
        
        # Parse row data
        columns = ['id', 'tracking_number', 'location', 'description', 'contact_info',
                  'image_path', 'gps_coordinates', 'ai_analysis', 'damage_types',
                  'severity_level', 'severity_score', 'repair_urgency', 'status',
                  'created_at', 'updated_at']
        
        report_data = dict(zip(columns, row))
        
        # Parse JSON fields
        try:
            if report_data['damage_types']:
                report_data['damage_types'] = json.loads(report_data['damage_types'])
        except:
            report_data['damage_types'] = []
        
        try:
            if report_data['ai_analysis']:
                report_data['ai_analysis'] = json.loads(report_data['ai_analysis'])
        except:
            report_data['ai_analysis'] = None
        
        try:
            if report_data['gps_coordinates']:
                report_data['gps_coordinates'] = json.loads(report_data['gps_coordinates'])
        except:
            report_data['gps_coordinates'] = None
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"Error getting report detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics', methods=['GET'])
def get_admin_analytics():
    """Get analytics data for admin dashboard"""
    try:
        conn = sqlite3.connect('road_reports.db')
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) FROM reports')
        total_reports = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM reports WHERE status = "completed"')
        completed_reports = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM reports WHERE severity_level = "high"')
        high_severity_reports = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT severity_level, COUNT(*) 
            FROM reports 
            WHERE severity_level != "unknown"
            GROUP BY severity_level
        ''')
        severity_distribution = dict(cursor.fetchall())
        
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM reports 
            GROUP BY status
        ''')
        status_distribution = dict(cursor.fetchall())
        
        # Get damage type distribution
        cursor.execute('SELECT damage_types FROM reports WHERE damage_types IS NOT NULL')
        damage_rows = cursor.fetchall()
        
        damage_type_counts = {}
        for row in damage_rows:
            try:
                types = json.loads(row[0]) if row[0] else []
                for damage_type in types:
                    damage_type_counts[damage_type] = damage_type_counts.get(damage_type, 0) + 1
            except:
                continue
        
        conn.close()
        
        # Calculate metrics
        completion_rate = (completed_reports / total_reports * 100) if total_reports > 0 else 0
        
        return jsonify({
            'total_reports': total_reports,
            'completed_reports': completed_reports,
            'high_severity_reports': high_severity_reports,
            'completion_rate': round(completion_rate, 1),
            'severity_distribution': severity_distribution,
            'status_distribution': status_distribution,
            'damage_type_distribution': damage_type_counts
        })
        
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/update-status', methods=['POST'])
def update_report_status():
    """Update report status"""
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        new_status = data.get('status')
        
        if not report_id or not new_status:
            return jsonify({'error': 'Missing report_id or status'}), 400
        
        conn = sqlite3.connect('road_reports.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE reports 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? OR tracking_number = ?
        ''', (new_status, report_id, report_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Report not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Status updated successfully'})
        
    except Exception as e:
        print(f"Error updating status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'pipeline_loaded': pipeline is not None,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("Starting RoadWatch Nigeria Backend...")
    print(f"Pipeline status: {'Loaded' if pipeline else 'Not loaded'}")
    print("Server starting on http://localhost:5000")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)