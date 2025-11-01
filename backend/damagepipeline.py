import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np
import time
from ultralytics import YOLO

class DamageSeverityCalculator:
    def __init__(self):
        # Severity rules for each damage type based on real-world impact
        self.damage_weights = {
            'pothole': {
                'base_severity': 0.8,      # High base - safety hazard
                'area_multiplier': 2.5,    # Size critical for potholes
                'count_penalty': 0.3       # Multiple potholes compound danger
            },
            'longitudinal_crack': {
                'base_severity': 0.3,      # Lower immediate danger
                'area_multiplier': 1.0,    # Length matters
                'count_penalty': 0.2       # Multiple cracks indicate wear
            },
            'lateral_crack': {
                'base_severity': 0.6,      # Structural concern
                'area_multiplier': 1.8,    # Width/length important
                'count_penalty': 0.4       # Multiple = foundation issues
            }
        }
        
        # Severity classification thresholds
        self.thresholds = {
            'low': 0.35,
            'medium': 0.65,
            'high': 0.85
        }
    
    def calculate_normalized_area(self, bbox, img_width, img_height):
        """Calculate detection area as percentage of image"""
        x1, y1, x2, y2 = bbox
        detection_area = (x2 - x1) * (y2 - y1)
        image_area = img_width * img_height
        return detection_area / image_area
    
    def calculate_detection_severity(self, detection, img_width, img_height):
        """Calculate severity score for single detection"""
        damage_type = detection['class']
        confidence = detection['confidence']
        bbox = detection['bbox']
        
        if damage_type not in self.damage_weights:
            return 0.5  # Default for unknown types
        
        weights = self.damage_weights[damage_type]
        area_ratio = self.calculate_normalized_area(bbox, img_width, img_height)
        
        # Severity calculation
        severity = weights['base_severity']
        severity += area_ratio * weights['area_multiplier']
        severity *= confidence  # Scale by detection confidence
        
        return min(severity, 1.0)  # Cap at 1.0
    
    def calculate_image_severity(self, detections, img_width, img_height):
        """Calculate overall severity for image with multiple detections"""
        if not detections:
            return {
                'severity_level': 'none',
                'severity_score': 0.0,
                'damage_counts': {},
                'dominant_damage': None,
                'repair_urgency': 'none'
            }
        
        # Group by damage type
        damage_groups = {}
        for detection in detections:
            damage_type = detection['class']
            if damage_type not in damage_groups:
                damage_groups[damage_type] = []
            damage_groups[damage_type].append(detection)
        
        # Calculate per-type severity
        type_severities = {}
        for damage_type, type_detections in damage_groups.items():
            if damage_type in self.damage_weights:
                weights = self.damage_weights[damage_type]
                
                # Individual severity scores
                individual_scores = [
                    self.calculate_detection_severity(det, img_width, img_height)
                    for det in type_detections
                ]
                
                # Aggregate severity for this type
                max_individual = max(individual_scores)
                count_factor = 1 + (len(type_detections) - 1) * weights['count_penalty']
                type_severity = min(max_individual * count_factor, 1.0)
                
                type_severities[damage_type] = {
                    'severity': type_severity,
                    'count': len(type_detections),
                    'max_individual': max_individual
                }
        
        # Calculate overall severity (weighted by damage type importance)
        if type_severities:
            weighted_sum = 0
            total_weight = 0
            
            for damage_type, metrics in type_severities.items():
                # Weight by base severity and detection count
                weight = (self.damage_weights[damage_type]['base_severity'] * 
                         (1 + 0.1 * metrics['count']))
                
                weighted_sum += metrics['severity'] * weight
                total_weight += weight
            
            overall_severity = weighted_sum / total_weight if total_weight > 0 else 0
        else:
            overall_severity = 0
        
        # Classify severity level
        if overall_severity >= self.thresholds['high']:
            severity_level = 'high'
            urgency = 'immediate'
        elif overall_severity >= self.thresholds['medium']:
            severity_level = 'medium'
            urgency = 'scheduled'
        elif overall_severity >= self.thresholds['low']:
            severity_level = 'low'
            urgency = 'routine'
        else:
            severity_level = 'minimal'
            urgency = 'monitoring'
        
        # Find dominant damage type
        dominant_damage = max(type_severities.keys(), 
                            key=lambda x: type_severities[x]['severity']) if type_severities else None
        
        return {
            'severity_level': severity_level,
            'severity_score': round(overall_severity, 3),
            'damage_counts': {k: v['count'] for k, v in type_severities.items()},
            'damage_severities': {k: round(v['severity'], 3) for k, v in type_severities.items()},
            'dominant_damage': dominant_damage,
            'repair_urgency': urgency,
            'total_detections': len(detections)
        }

class RoadDamagePipeline:
    def __init__(self, road_classifier_path, yolo_model_path):
        """
        Initialize the complete pipeline
        
        Args:
            road_classifier_path: Path to your HuggingFace road classifier
            yolo_model_path: Path to your trained YOLO model (.pt file)
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize components
        self.road_classifier = self.load_road_classifier(road_classifier_path)
        self.yolo_model = YOLO(yolo_model_path)
        self.severity_calculator = DamageSeverityCalculator()
        
        print(f"Pipeline initialized on {self.device}")
        print(f"Road classifier loaded: {'Success' if self.road_classifier else 'Failed'}")
        print(f"YOLO model loaded: {'Success' if self.yolo_model else 'Failed'}")
    
    def load_road_classifier(self, model_path):
        """Load your road classifier from HuggingFace"""
        try:
            print(f"Loading road classifier from: {model_path}")
            
            # Download the model file from HuggingFace
            from huggingface_hub import hf_hub_download
            model_file = hf_hub_download(
                repo_id=model_path, 
                filename="pytorch_model.pth"
            )
            
            checkpoint = torch.load(model_file, map_location=self.device)
            
            # Recreate your road classifier architecture
            class RoadClassifier(nn.Module):
                def __init__(self, num_classes=2):
                    super(RoadClassifier, self).__init__()
                    self.backbone = models.resnet18(pretrained=False)
                    self.backbone.fc = nn.Linear(self.backbone.fc.in_features, num_classes)
                    self.dropout = nn.Dropout(0.5)
                
                def forward(self, x):
                    x = self.backbone.conv1(x)
                    x = self.backbone.bn1(x)
                    x = self.backbone.relu(x)
                    x = self.backbone.maxpool(x)
                    
                    x = self.backbone.layer1(x)
                    x = self.backbone.layer2(x)
                    x = self.backbone.layer3(x)
                    x = self.backbone.layer4(x)
                    
                    x = self.backbone.avgpool(x)
                    x = torch.flatten(x, 1)
                    x = self.dropout(x)
                    x = self.backbone.fc(x)
                    
                    return x
            
            # Load model
            model = RoadClassifier().to(self.device)
            
            # Handle different checkpoint formats
            if 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            else:
                model.load_state_dict(checkpoint)
            
            model.eval()
            
            # Define transforms (same as training)
            self.road_transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            
            print("Road classifier loaded successfully")
            return model
            
        except Exception as e:
            print(f"Error loading road classifier: {e}")
            return None
    
    def is_road_image(self, image_path_or_pil, threshold=0.5):
        """
        Check if image contains a road surface
        
        Args:
            image_path_or_pil: Path to image file or PIL Image object
            threshold: Confidence threshold for road classification
            
        Returns:
            dict: Classification result with confidence
        """
        if self.road_classifier is None:
            return {
                'is_road': True,  # Skip check if classifier not loaded
                'confidence': 1.0,
                'message': 'Road classifier not available - proceeding with damage detection'
            }
        
        try:
            # Load and preprocess image
            if isinstance(image_path_or_pil, str):
                image = Image.open(image_path_or_pil).convert('RGB')
            else:
                image = image_path_or_pil.convert('RGB')
            
            # Apply transforms
            input_tensor = self.road_transform(image).unsqueeze(0).to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = self.road_classifier(input_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                road_confidence = float(probabilities[0][1])  # Assuming class 1 is 'road'
                
                is_road = road_confidence >= threshold
                
                return {
                    'is_road': is_road,
                    'confidence': road_confidence,
                    'non_road_confidence': float(probabilities[0][0]),
                    'message': f"{'Road surface detected' if is_road else 'Non-road surface detected'}"
                }
                
        except Exception as e:
            print(f"Error in road classification: {e}")
            return {
                'is_road': True,  # Default to proceeding
                'confidence': 0.5,
                'message': f'Road classification failed: {e}'
            }
    
    def detect_damage(self, image_path):
        """
        Detect damage using YOLO model
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Detection results
        """
        try:
            # Run YOLO detection
            results = self.yolo_model.predict(image_path, conf=0.15, verbose=False)
            
            # Parse results
            detections = []
            if len(results) > 0 and len(results[0].boxes) > 0:
                img_height, img_width = results[0].orig_shape
                
                for box in results[0].boxes:
                    detection = {
                        'class': self.yolo_model.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].cpu().numpy().tolist(),
                        'center': [
                            float((box.xyxy[0][0] + box.xyxy[0][2]) / 2),
                            float((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                        ]
                    }
                    detections.append(detection)
            else:
                img_height, img_width = 480, 640  # Default
            
            return {
                'detections': detections,
                'image_dimensions': [img_width, img_height],
                'total_detections': len(detections),
                'damage_types': list(set([d['class'] for d in detections]))
            }
            
        except Exception as e:
            print(f"Error in damage detection: {e}")
            return {
                'detections': [],
                'image_dimensions': [640, 480],
                'total_detections': 0,
                'damage_types': [],
                'error': str(e)
            }
    
    def calculate_severity(self, detections, img_width, img_height):
        """Calculate damage severity"""
        return self.severity_calculator.calculate_image_severity(
            detections, img_width, img_height
        )
    
    def analyze_image(self, image_path):
        """
        Complete pipeline analysis
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Complete analysis results
        """
        analysis_start_time = time.time()
        
        result = {
            'image_path': image_path,
            'timestamp': time.time(),
            'pipeline_stages': {}
        }
        
        try:
            # Stage 1: Road Classification
            road_result = self.is_road_image(image_path)
            result['pipeline_stages']['road_classification'] = road_result
            
            if not road_result['is_road']:
                result['status'] = 'rejected'
                result['message'] = f"Non-road surface detected (confidence: {road_result['confidence']:.1%})"
                return result
            
            # Stage 2: Damage Detection
            damage_result = self.detect_damage(image_path)
            result['pipeline_stages']['damage_detection'] = damage_result
            
            if damage_result['total_detections'] == 0:
                result['status'] = 'no_damage'
                result['message'] = "No road damage detected"
                result['severity_assessment'] = {
                    'severity_level': 'none',
                    'severity_score': 0.0,
                    'repair_urgency': 'none'
                }
                return result
            
            # Stage 3: Severity Assessment
            severity_result = self.calculate_severity(
                damage_result['detections'],
                damage_result['image_dimensions'][0],
                damage_result['image_dimensions'][1]
            )
            result['pipeline_stages']['severity_assessment'] = severity_result
            
            # Final result compilation
            result['status'] = 'completed'
            result['summary'] = {
                'total_damages': damage_result['total_detections'],
                'damage_types': damage_result['damage_types'],
                'severity_level': severity_result['severity_level'],
                'severity_score': severity_result['severity_score'],
                'repair_urgency': severity_result['repair_urgency'],
                'dominant_damage': severity_result.get('dominant_damage', 'N/A')
            }
            
            # Generate actionable output
            result['recommendations'] = self.generate_recommendations(severity_result)
            result['processing_time'] = f"{time.time() - analysis_start_time:.2f}s"
            
            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"Pipeline error: {str(e)}"
            return result
    
    def generate_recommendations(self, severity_result):
        """Generate recommendations based on severity"""
        recommendations = []
        
        urgency = severity_result['repair_urgency']
        damage_counts = severity_result.get('damage_counts', {})
        
        if urgency == 'immediate':
            recommendations.append("URGENT: Immediate repair required within 24-48 hours")
            recommendations.append("Consider temporary traffic control measures")
        elif urgency == 'scheduled':
            recommendations.append("Schedule repair within 2-4 weeks")
            recommendations.append("Monitor for deterioration")
        elif urgency == 'routine':
            recommendations.append("Include in routine maintenance cycle")
            recommendations.append("Re-inspect in 3-6 months")
        else:
            recommendations.append("Continue regular monitoring")
        
        # Damage-specific recommendations
        if 'pothole' in damage_counts:
            count = damage_counts['pothole']
            recommendations.append(f"Pothole repair needed ({count} location{'s' if count > 1 else ''})")
        
        if 'lateral_crack' in damage_counts:
            recommendations.append("Lateral cracks may indicate structural issues")
        
        if 'longitudinal_crack' in damage_counts:
            count = damage_counts['longitudinal_crack']
            if count > 2:
                recommendations.append("Multiple longitudinal cracks - consider surface overlay")
        
        return recommendations

def initialize_pipeline(road_classifier_path=None, yolo_model_path=None):
    """Initialize the complete road damage analysis pipeline"""
    
    try:
        # Default paths - update these for your models
        if road_classifier_path is None:
            road_classifier_path = "tomunizua/road-classification_filter"
        
        if yolo_model_path is None:
            # You need to set this to your actual YOLO model path
            yolo_model_path = "models/best.pt"  # UPDATE THIS PATH
        
        print("Initializing Road Damage Analysis Pipeline...")
        print(f"Road Classifier: {road_classifier_path}")
        print(f"YOLO Model: {yolo_model_path}")
        
        pipeline = RoadDamagePipeline(road_classifier_path, yolo_model_path)
        
        print("Pipeline initialization complete!")
        return pipeline
        
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        return None

if __name__ == "__main__":
    # Test the pipeline
    pipeline = initialize_pipeline()
    
    if pipeline:
        print("Pipeline ready for use!")
        # Example usage:
        # result = pipeline.analyze_image("path/to/road/image.jpg")
        # print(result)
    else:
        print("Pipeline initialization failed")