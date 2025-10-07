from flask_sqlalchemy import SQLAlchemy
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
    
    # AI prediction results
    damage_detected = db.Column(db.Boolean, nullable=False)
    damage_type = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    severity_score = db.Column(db.Integer, nullable=False)
    estimated_cost = db.Column(db.Integer, nullable=False)
    
    # Status tracking
    status = db.Column(db.String(50), default='submitted', nullable=False)
    # Possible statuses: submitted, under_review, scheduled, in_progress, completed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'tracking_number': self.tracking_number,
            'location': self.location,
            'description': self.description,
            'damage_type': self.damage_type,
            'confidence': self.confidence,
            'severity_score': self.severity_score,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }