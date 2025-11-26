from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(50), unique=True, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # --- NEW COLUMNS ---
    user_reported_size = db.Column(db.String(50), nullable=True)
    severity_level = db.Column(db.String(50), nullable=True)
    repair_urgency = db.Column(db.String(50), nullable=True)
    # -------------------

    # Location Data
    state = db.Column(db.String(50), default='Lagos', nullable=False)
    lga = db.Column(db.String(100), nullable=True)
    gps_latitude = db.Column(db.Float, nullable=True)
    gps_longitude = db.Column(db.Float, nullable=True)
    gps_detected = db.Column(db.Boolean, default=False, nullable=False)
    
    # AI Results
    damage_detected = db.Column(db.Boolean, nullable=False, default=False)
    damage_type = db.Column(db.String(100), nullable=False, default='processing')
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    severity_score = db.Column(db.Integer, nullable=False, default=0)
    estimated_cost = db.Column(db.Integer, nullable=False, default=0)
    
    # Admin Status
    assigned_contractor = db.Column(db.String(100), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='submitted', nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='administrator', nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ReportSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Report
        include_relationships = True
        load_instance = True
        datetimeformat = '%Y-%m-%d %H:%M:%S'