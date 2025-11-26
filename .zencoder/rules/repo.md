---
description: Repository Information Overview
alwaysApply: true
---

# RoadWatch Nigeria Information

## Summary
RoadWatch Nigeria is an AI-powered infrastructure damage reporting and management system designed to empower Nigerian citizens to report road damage. The system uses machine learning to analyze submitted images, detect damage, estimate severity, and calculate repair costs. It includes a citizen portal for reporting and an admin dashboard for managing reports and optimizing repair budgets.

## Structure
- **backend/**: Flask API server with ML pipeline and database
- **frontend/**: HTML/TailwindCSS web interfaces
- **models/**: Trained ML models for damage detection
- **notebooks/**: Jupyter notebooks for ML model development
- **data/**: Raw and processed datasets
- **scripts/**: Utility scripts for data processing

## Language & Runtime
**Language**: Python
**Version**: 3.10.0
**Framework**: Flask
**Package Manager**: pip

## Dependencies
**Main Dependencies**:
- Flask, Flask-SQLAlchemy, Flask-Cors, Flask-HTTPAuth
- TensorFlow/Keras for ML model
- PuLP for optimization algorithms
- Ultralytics/YOLOv8 for object detection
- Pillow, NumPy, Pandas for data processing

**Development Dependencies**:
- Jupyter Notebooks
- Matplotlib, Seaborn for visualization
- Optuna for hyperparameter tuning
- Wandb for experiment tracking

## Build & Installation
```bash
# Clone repository
git clone https://github.com/tomunizua/road-infra-ng.git
cd road-infra-ng

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
cd backend
python app.py
```

## Database
**Type**: SQLite
**Schema**: Reports table with fields for tracking, image, location, damage detection, severity, cost estimation, and repair status
**Production Plan**: Migration to PostgreSQL recommended for production

## ML Pipeline
**Model**: YOLOv8 for road damage detection
**Features**: 
- Automatic damage detection (potholes, cracks)
- Severity scoring (1-10 scale)
- Cost estimation based on damage type and severity
- Budget optimization using linear programming

## Testing
**Framework**: Built-in Python unittest
**Test Files**: Located in backend/ directory (test_db.py, test_budget_pipeline.py)
**Run Command**:
```bash
cd backend
python -m unittest test_budget_pipeline.py
```

## Frontend
**Technology**: HTML, TailwindCSS, Vanilla JavaScript
**Components**:
- Citizen Portal: Public interface for submitting reports
- Admin Dashboard: Secure interface for managing reports and budget
**Authentication**: Basic HTTP Authentication for admin routes