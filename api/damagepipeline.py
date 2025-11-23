import requests
import base64
import time
import logging
import os
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# 1. Get your free API Key from: https://app.roboflow.com/settings/api
# 2. Add 'ROBOFLOW_API_KEY' to your Render Environment Variables
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "YOUR_PRIVATE_API_KEY_HERE") 

# USING GROUP12 POTHOLE MODEL (High Accuracy for Potholes)
MODEL_ID = "pothole-detection-bnahf/1" 

class RoadDamagePipeline:
    def __init__(self, road_classifier_path=None, yolo_model_path=None):
        print(f"🚀 Initialized Roboflow Cloud Pipeline (Model: {MODEL_ID})")
        print("   (Specialized Pothole Detection Model - High mAP)")
    
    def map_class_to_system(self, roboflow_class):
        """
        Maps model classes to your system's standard types.
        Since this model is pothole-only, we map everything to 'pothole'.
        """
        # This specific model usually returns 'Pothole' or 'pothole'
        # But regardless of what it calls it, we know it's a pothole.
        return 'pothole'

    def analyze_image(self, image_path):
        analysis_start_time = time.time()
        
        result = {
            'image_path': image_path,
            'timestamp': time.time(),
            'pipeline_stages': {'damage_detection': {'detections': []}},
            'status': 'error',
            'summary': {
                'total_damages': 0,
                'damage_types': [],
                'dominant_damage': 'none',
                'severity_level': 'none',
                'severity_score': 0
            }
        }
        
        try:
            # 1. Encode image to base64 for API
            with open(image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode("utf-8")

            # 2. Call Roboflow Inference API
            # We can use a higher confidence (40-50%) because this model is accurate
            url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={ROBOFLOW_API_KEY}&confidence=40"
            
            response = requests.post(url, data=img_data, headers={
                "Content-Type": "application/x-www-form-urlencoded"
            })

            if response.status_code != 200:
                logger.error(f"Roboflow API Error: {response.text}")
                result['message'] = f"AI Provider Error: {response.text}"
                # Fallback: Return 'completed' so system doesn't crash
                result['status'] = 'completed' 
                return result

            predictions = response.json().get('predictions', [])
            
            # 3. Map Roboflow output to System Format
            detections = []
            
            for pred in predictions:
                # Map Class Name (Everything becomes 'pothole')
                system_class = self.map_class_to_system(pred['class'])
                
                # Convert Coordinates: Center-XYWH -> Corner-XYXY
                # Roboflow returns: x (center), y (center), width, height
                # System needs: x1 (left), y1 (top), x2 (right), y2 (bottom)
                half_w = pred['width'] / 2
                half_h = pred['height'] / 2
                
                bbox = [
                    pred['x'] - half_w,  # x1
                    pred['y'] - half_h,  # y1
                    pred['x'] + half_w,  # x2
                    pred['y'] + half_h   # y2
                ]

                detections.append({
                    'class': system_class,
                    'original_class': pred['class'],
                    'confidence': pred['confidence'],
                    'bbox': bbox
                })

            # 4. Generate Summary
            damage_types = list(set([d['class'] for d in detections]))
            
            # Determine dominant damage
            dominant_damage = 'none'
            if detections:
                dominant_damage = 'pothole' # Since that's all we detect now

            result['pipeline_stages']['damage_detection']['detections'] = detections
            result['summary'] = {
                'total_damages': len(detections),
                'damage_types': damage_types,
                'dominant_damage': dominant_damage,
                'severity_level': 'calculating...', 
                'severity_score': 0 
            }
            
            if len(detections) > 0:
                result['status'] = 'completed'
            else:
                result['status'] = 'no_damage'
                
            result['processing_time'] = f"{time.time() - analysis_start_time:.2f}s"
            logger.info(f"AI Success: Found {len(detections)} damages")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            result['message'] = str(e)
            return result

# --- FACTORY FUNCTION ---
def initialize_pipeline(road_classifier_path=None, yolo_model_path=None):
    return RoadDamagePipeline()


# =============================================================================
# 🔻 ARCHIVED: LOCAL YOLO PIPELINE (COMMENTED OUT FOR REFERENCE) 🔻
# =============================================================================
"""
import torch
from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel

class DamageSeverityCalculator:
    def __init__(self):
        self.damage_weights = {
            'pothole': {'base_severity': 0.8, 'area_multiplier': 2.5, 'count_penalty': 0.3},
            'longitudinal_crack': {'base_severity': 0.3, 'area_multiplier': 1.0, 'count_penalty': 0.2},
            'lateral_crack': {'base_severity': 0.6, 'area_multiplier': 1.8, 'count_penalty': 0.4}
        }
        self.thresholds = {'low': 0.35, 'medium': 0.65, 'high': 0.85}
    
    # ... (Previous calculation methods) ...

class LocalRoadDamagePipeline:
    def __init__(self, road_classifier_path, yolo_model_path):
        # This requires PyTorch and uses ~800MB RAM
        self.device = torch.device('cpu')
        try:
            # Fix for PyTorch 2.6+ security restriction
            torch.serialization.add_safe_globals([DetectionModel])
        except:
            pass
            
        self.yolo_model = YOLO(yolo_model_path) 
        self.severity_calculator = DamageSeverityCalculator()
        print(f"Local Pipeline initialized on {self.device}")

    def analyze_image(self, image_path):
        # ... (Previous local analysis logic) ...
        pass
"""