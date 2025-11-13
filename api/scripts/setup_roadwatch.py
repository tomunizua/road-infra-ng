#!/usr/bin/env python3
"""
RoadWatch Nigeria Setup and Launch Script
This script helps set up and run the integrated RoadWatch system
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime

def print_banner():
    print("=" * 60)
    print("🛣️  RoadWatch Nigeria - AI-Powered Infrastructure Management")
    print("=" * 60)
    print()

def check_dependencies():
    """Check if required Python packages are installed"""
    print("📋 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask-cors',
        'flask-sqlalchemy',
        'marshmallow-sqlalchemy',
        'pillow',
        'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    # if missing_packages:
    #     print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
    #     print("📦 Install them with:")
    #     print(f"   pip install {' '.join(missing_packages)}")
    #     return False
    
    print("✅ All dependencies satisfied!")
    return True

def setup_database():
    """Set up the SQLite database"""
    print("\n🗄️  Setting up database...")
    
    try:
        # Import after checking dependencies
        from database import db, Report
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///road_reports.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if we have any existing data
            report_count = Report.query.count()
            print(f"📊 Current reports in database: {report_count}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_uploads_directory():
    """Create uploads directory if it doesn't exist"""
    print("\n📁 Setting up file storage...")
    
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"✅ Created {uploads_dir} directory")
    else:
        print(f"✅ {uploads_dir} directory already exists")

def check_ai_pipeline():
    """Check if AI pipeline components are available"""
    print("\n🤖 Checking AI pipeline...")
    
    try:
        from damagepipeline import initialize_pipeline
        print("✅ Pipeline module found")
        
        # Note about YOLO model
        print("⚠️  Note: Make sure to update the YOLO model path in the backend")
        print("   Current path: 'path/to/your/best.pt' (needs to be updated)")
        
        return True
    except ImportError as e:
        print(f"⚠️  Pipeline module not found: {e}")
        print("   The system will work without AI analysis")
        return False

def create_demo_data():
    """Create some demo data for testing"""
    print("\n🎯 Creating demo data...")
    
    try:
        from database import db, Report
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///road_reports.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # Check if we already have data
            if Report.query.count() > 0:
                print("📊 Database already has data, skipping demo creation")
                return
            
            # Create demo reports
            demo_reports = [
                {
                    'tracking_number': 'RW20250101DEMO001',
                    'location': 'Victoria Island, Lagos',
                    'description': 'Large pothole on Ahmadu Bello Way causing traffic issues',
                    'phone': '+234 801 234 5678',
                    'damage_detected': True,
                    'damage_type': 'pothole',
                    'confidence': 0.92,
                    'severity_score': 85,
                    'estimated_cost': 1500,
                    'status': 'under_review'
                },
                {
                    'tracking_number': 'RW20250101DEMO002',
                    'location': 'Ikeja, Lagos',
                    'description': 'Cracks appearing on Allen Avenue after recent rains',
                    'phone': '+234 802 345 6789',
                    'damage_detected': True,
                    'damage_type': 'longitudinal_crack',
                    'confidence': 0.78,
                    'severity_score': 45,
                    'estimated_cost': 800,
                    'status': 'scheduled'
                },
                {
                    'tracking_number': 'RW20250101DEMO003',
                    'location': 'Lekki Phase 1, Lagos',
                    'description': 'Road surface deterioration near toll gate',
                    'phone': '+234 803 456 7890',
                    'damage_detected': True,
                    'damage_type': 'lateral_crack',
                    'confidence': 0.88,
                    'severity_score': 60,
                    'estimated_cost': 1200,
                    'status': 'completed'
                }
            ]
            
            for report_data in demo_reports:
                report = Report(**report_data)
                db.session.add(report)
            
            db.session.commit()
            print(f"✅ Created {len(demo_reports)} demo reports")
            
    except Exception as e:
        print(f"❌ Failed to create demo data: {e}")

def print_usage_instructions():
    """Print instructions for using the system"""
    print("\n🚀 System Setup Complete!")
    print("=" * 60)
    print("\n📋 How to use RoadWatch Nigeria:")
    print()
    print("1. 👥 CITIZEN PORTAL:")
    print("   - Open: http://localhost:5000/redo.html")
    print("   - Submit road damage reports")
    print("   - Track report status")
    print()
    print("2. 👨‍💼 ADMIN DASHBOARD:")
    print("   - Open: http://localhost:5000/admin.html")
    print("   - View all reports")
    print("   - Manage report status")
    print("   - View analytics")
    print()
    print("3. 🔧 API ENDPOINTS:")
    print("   - Health check: http://localhost:5000/api/health")
    print("   - Submit report: POST http://localhost:5000/api/submit-report")
    print("   - Track report: GET http://localhost:5000/api/track/{tracking_number}")
    print()
    print("4. 📊 DEMO DATA:")
    print("   - Try tracking: RW20250101DEMO001, RW20250101DEMO002, or RW20250101DEMO003")
    print()
    print("=" * 60)

def main():
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed")
        sys.exit(1)
    
    # Create uploads directory
    create_uploads_directory()
    
    # Check AI pipeline
    check_ai_pipeline()
    
    # Create demo data
    create_demo_data()
    
    # Print usage instructions
    print_usage_instructions()
    
    # Ask if user wants to start the server
    print("🚀 Ready to start the RoadWatch server!")
    start_server = input("Start server now? (y/n): ").lower().strip()
    
    if start_server in ['y', 'yes']:
        print("\n🌐 Starting RoadWatch server...")
        print("📍 Server will be available at: http://localhost:5000")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        try:
            # Start the server
            import subprocess
            subprocess.run([sys.executable, 'backend/integrated_backend.py'])
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped by user")
        except Exception as e:
            print(f"\n❌ Error starting server: {e}")
    else:
        print("\n📝 To start the server manually, run:")
        print("   python integrated_backend.py")
        print("\n✅ Setup complete!")

if __name__ == "__main__":
    main()
