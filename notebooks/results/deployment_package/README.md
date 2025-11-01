# Road Damage Detection Model - Deployment Package

## Model Information
- Model Type: YOLOv8 (yolov8s)
- Input Size: 640x640
- Classes: 3 damage types
- Training Date: 2025-10-28
- Optimized for class imbalance with focal loss

## Files Included
- `road_damage_model.pt`: Trained YOLOv8 model
- `config.json`: Model configuration and metadata
- `inference.py`: Python inference script
- `README.md`: This file

## Quick Start
```python
from inference import RoadDamageDetector

# Initialize detector
detector = RoadDamageDetector('road_damage_model.pt', 'config.json')

# Detect damage in image
result = detector.detect_damage('your_image.jpg')
print(f"Severity Score: {result['severity_score']}/100")
print(f"Damage Count: {result['damage_count']}")
print(f"Recommendations: {result['recommendations']}")
```

## Requirements
- ultralytics
- opencv-python
- numpy

## Installation
```bash
pip install ultralytics opencv-python numpy
```

## Damage Classes
{
  "0": "pothole",
  "1": "longitudinal_crack",
  "2": "lateral_crack"
}

## Class Imbalance Handling
This model was trained with focal loss to address class imbalance:
- Original distribution: ~53% longitudinal crack, 26% pothole, 20% lateral crack
- Focal loss gamma: 2.0
- Enhanced augmentation for minority classes

## Performance Metrics
{
  "mAP50": 0.4170775460753122,
  "mAP50-95": 0.18355572540669052,
  "precision": 0.42758065822948627,
  "recall": 0.4124168514412417,
  "f1_score": 0.4198618847651174,
  "accuracy": 0.4170775460753122
}

## Severity Weights
{
  "pothole": 3.0,
  "alligator_crack": 2.5,
  "longitudinal_crack": 1.5,
  "lateral_crack": 1.5,
  "crack": 2.0,
  "manhole": 1.0
}
