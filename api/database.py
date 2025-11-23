from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

db = SQLAlchemy()

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(50), unique=True, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # GPS and Location fields
    state = db.Column(db.String(50), default='Lagos', nullable=False)
    lga = db.Column(db.String(100), nullable=True)
    gps_latitude = db.Column(db.Float, nullable=True)
    gps_longitude = db.Column(db.Float, nullable=True)
    gps_detected = db.Column(db.Boolean, default=False, nullable=False)
    
    # AI prediction results (Core)
    damage_detected = db.Column(db.Boolean, nullable=False)
    damage_type = db.Column(db.String(100), nullable=False) # Dominant type
    confidence = db.Column(db.Float, nullable=False)
    severity_score = db.Column(db.Integer, nullable=False)
    estimated_cost = db.Column(db.Integer, nullable=False)
    
    # --- NEW FIELDS FOR PIPELINE SYNC ---
    # These align with the output from damagepipeline.py
    severity_level = db.Column(db.String(20), nullable=True) # 'high', 'medium', 'low', 'minimal'
    repair_urgency = db.Column(db.String(20), nullable=True) # 'immediate', 'scheduled', 'routine'
    
    # Store the detailed counts (e.g., {'pothole': 2, 'crack': 1})
    # Using JSON type allows storing the dictionary directly.
    # Note: If using SQLite locally, SQLAlchemy handles JSON serialization automatically.
    damage_counts = db.Column(db.JSON, nullable=True) 
    # ------------------------------------

    # Admin-controlled fields
    assigned_contractor = db.Column(db.String(100), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(50), default='under_review', nullable=False)
    # Possible statuses: under_review, scheduled, completed, rejected
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, exclude=None):
        if exclude is None:
            exclude = []
        
        data = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    data[column.name] = value.isoformat()
                else:
                    data[column.name] = value
        return data


class ReportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Report
        include_relationships = True
        load_instance = True
        # Customize date format for output
        datetimeformat = '%Y-%m-%d %H:%M:%S'

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