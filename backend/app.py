from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import os
from datetime import datetime
from database import db, Report
from ml_pipeline import calculate_severity, estimate_repair_cost, optimize_repair_budget, generate_repair_schedule

app = Flask(__name__)

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Go up one level to project root

# Configure database
DB_PATH = os.path.join(BASE_DIR, 'roadwatch.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')

# Initialize database
db.init_app(app)

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Explicit CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Load model with proper path handling
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'pothole_baseline_v1.h5')

try:
    if os.path.exists(MODEL_PATH):
        print(f"Loading model from: {MODEL_PATH}")
        model = load_model(MODEL_PATH)
        print("Model loaded successfully!")
    else:
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print(f"Current directory: {os.getcwd()}")
        print(f"BASE_DIR: {BASE_DIR}")
        print(f"PROJECT_ROOT: {PROJECT_ROOT}")
        model = None
except Exception as e:
    print(f"ERROR loading model: {e}")
    model = None

# Create database tables
with app.app_context():
    db.create_all()
    print("Database initialized!")

def generate_tracking_number():
    """Generate unique tracking number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_digits = str(np.random.randint(1000, 9999))
    return f'RW-{timestamp}-{random_digits}'

@app.route('/api/predict', methods=['POST', 'OPTIONS'])
def predict():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        print("\n=== NEW PREDICTION REQUEST ===")
        
        # Check if model is loaded
        if model is None:
            return jsonify({'error': 'Model not loaded. Check server logs.'}), 500
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        location = request.form.get('location', '')
        description = request.form.get('description', '')
        phone = request.form.get('phone', '')
        
        print(f"Location: {location}")
        print(f"Description: {description}")
        
        # Save uploaded image
        tracking_number = generate_tracking_number()
        filename = f"{tracking_number}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"Image saved: {filepath}")
        
        # Read and preprocess image for prediction
        img = Image.open(filepath)
        img_resized = img.resize((224, 224))
        img_array = np.array(img_resized) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # ML MODEL PREDICTION
        prediction = model.predict(img_array, verbose=0)[0][0]
        print(f"Raw prediction: {prediction}")
        
        # Determine result
        is_pothole = bool(prediction > 0.5)
        confidence = float(prediction if is_pothole else (1 - prediction))
        
        print(f"Is pothole: {is_pothole}, Confidence: {confidence}")
        
        # CALCULATE SEVERITY using ML confidence
        severity = calculate_severity(confidence * 100, is_pothole)
        print(f"Severity: {severity}")
        
        # ESTIMATE COST based on severity
        cost = estimate_repair_cost(severity, 'Pothole')
        print(f"Estimated cost: ₦{cost:,}")
        
        # Create database record
        report = Report(
            tracking_number=tracking_number,
            image_filename=filename,
            location=location,
            description=description,
            phone=phone,
            damage_detected=is_pothole,
            damage_type='Pothole' if is_pothole else 'Normal Road',
            confidence=confidence * 100,
            severity_score=severity,
            estimated_cost=cost,
            status='under_review'
        )
        
        db.session.add(report)
        db.session.commit()
        
        result = {
            'tracking_number': tracking_number,
            'damage_detected': is_pothole,
            'confidence': round(confidence * 100, 2),
            'severity_score': severity,
            'estimated_cost': cost,
            'damage_type': report.damage_type
        }
        
        print("Success! Report created:", result)
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in predict: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimize', methods=['POST', 'OPTIONS'])
def optimize_budget():
    """
    Run budget optimization on all pending reports
    Returns optimal repair schedule
    """
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        print("\n=== OPTIMIZATION REQUEST ===")
        data = request.get_json()
        budget = data.get('budget', 1000000)  # Default ₦1M budget
        
        print(f"Budget: ₦{budget:,}")
        
        # Get all reports with damage
        reports = Report.query.filter_by(
            damage_detected=True,
            status='under_review'
        ).all()
        
        print(f"Found {len(reports)} reports to optimize")
        
        # Prepare for optimization
        report_data = [{
            'id': r.id,
            'tracking_number': r.tracking_number,
            'severity_score': r.severity_score,
            'estimated_cost': r.estimated_cost,
            'location': r.location,
            'damage_type': r.damage_type,
            'damage_detected': r.damage_detected
        } for r in reports]
        
        # Run optimization
        schedule = generate_repair_schedule(report_data, budget)
        
        print(f"Optimization complete:")
        print(f"   - Repairs scheduled: {schedule['repairs_count']}")
        print(f"   - Total cost: ₦{schedule['total_cost']:,}")
        print(f"   - Budget utilization: {schedule['budget_utilization']:.1f}%")
        
        return jsonify(schedule)
        
    except Exception as e:
        print(f"ERROR in optimize: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/track/<tracking_number>', methods=['GET'])
def track_report(tracking_number):
    """Get report status by tracking number"""
    report = Report.query.filter_by(tracking_number=tracking_number).first()
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    return jsonify(report.to_dict())

@app.route('/api/reports', methods=['GET'])
def get_all_reports():
    """Get all reports (for admin dashboard)"""
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return jsonify([report.to_dict() for report in reports])

@app.route('/api/reports/recent', methods=['GET'])
def get_recent_reports():
    """Get 10 most recent reports (for citizen portal)"""
    reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
    return jsonify([{
        'location': report.location,
        'damage_type': report.damage_type,
        'status': report.status,
        'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for report in reports])

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'database': 'connected',
        'upload_folder': app.config['UPLOAD_FOLDER']
    })

@app.route('/api/test-ml', methods=['GET'])
def test_ml():
    """Test ML pipeline functions"""
    try:
        # Test severity calculation
        severity_low = calculate_severity(55, True)
        severity_high = calculate_severity(95, True)
        
        # Test cost estimation
        cost_low = estimate_repair_cost(3, 'Pothole')
        cost_high = estimate_repair_cost(9, 'Pothole')
        
        # Test optimization with dummy data
        dummy_reports = [
            {'id': 1, 'severity': 8, 'cost': 50000, 'location': 'Test 1'},
            {'id': 2, 'severity': 5, 'cost': 30000, 'location': 'Test 2'},
            {'id': 3, 'severity': 9, 'cost': 80000, 'location': 'Test 3'},
        ]
        opt_result = optimize_repair_budget(dummy_reports, 100000)
        
        return jsonify({
            'severity_calculation': {
                'low_confidence': severity_low,
                'high_confidence': severity_high
            },
            'cost_estimation': {
                'low_severity': cost_low,
                'high_severity': cost_high
            },
            'optimization_test': opt_result,
            'status': 'All ML functions working!'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Starting Road Infrastructure API")
    print("="*50)
    print(f"Model path: {MODEL_PATH}")
    print(f"Database: {DB_PATH}")
    print(f"Uploads folder: {app.config['UPLOAD_FOLDER']}")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')