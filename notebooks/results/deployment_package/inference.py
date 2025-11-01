#!/usr/bin/env python3
"""
Road Damage Detection Inference Script
Optimized for class imbalance with focal loss training
"""

import cv2
import numpy as np
import json
from pathlib import Path
from ultralytics import YOLO

class RoadDamageDetector:
    def __init__(self, model_path, config_path=None):
        self.model = YOLO(model_path)
        
        # Load configuration
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'model_info': {
                    'class_names': {0: 'pothole', 1: 'longitudinal_crack', 2: 'lateral_crack'}
                },
                'inference_config': {
                    'confidence_threshold': 0.5,
                    'iou_threshold': 0.5
                },
                'severity_weights': {'pothole': 3.0, 'alligator_crack': 2.5, 'longitudinal_crack': 1.5, 'lateral_crack': 1.5, 'crack': 2.0, 'manhole': 1.0}
            }
        
        self.class_names = self.config['model_info']['class_names']
        self.severity_weights = self.config['severity_weights']
    
    def detect_damage(self, image_path, conf_threshold=None, iou_threshold=None):
        """
        Detect road damage in an image
        """
        conf = conf_threshold or self.config['inference_config']['confidence_threshold']
        iou = iou_threshold or self.config['inference_config']['iou_threshold']
        
        # Run inference
        results = self.model(image_path, conf=conf, iou=iou)
        
        if not results or len(results) == 0:
            return {
                'damage_count': 0,
                'severity_score': 0,
                'severity_level': 'No Damage',
                'detections': [],
                'recommendations': ['No maintenance required']
            }
        
        result = results[0]
        detections = []
        
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = float(box.conf.item())
                
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Convert to normalized center format
                img_h, img_w = result.orig_shape
                x_center = ((x1 + x2) / 2) / img_w
                y_center = ((y1 + y2) / 2) / img_h
                width = (x2 - x1) / img_w
                height = (y2 - y1) / img_h
                
                class_name = self.class_names.get(str(class_id), f'damage_{class_id}')
                
                detections.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'normalized_bbox': [x_center, y_center, width, height]
                })
        
        # Calculate severity
        severity_result = self._calculate_severity(detections, result.orig_shape)
        
        return {
            'damage_count': len(detections),
            'detections': detections,
            **severity_result
        }
    
    def _calculate_severity(self, detections, img_shape):
        """
        Calculate severity score based on detections
        """
        if not detections:
            return {
                'severity_score': 0,
                'severity_level': 'No Damage',
                'recommendations': ['No maintenance required']
            }
        
        img_h, img_w = img_shape
        weighted_score = 0
        total_area = 0
        damage_types = {}
        
        for detection in detections:
            class_name = detection['class_name']
            confidence = detection['confidence']
            x_center, y_center, width, height = detection['normalized_bbox']
            
            # Count damage types
            damage_types[class_name] = damage_types.get(class_name, 0) + 1
            
            # Calculate weighted score
            class_weight = self.severity_weights.get(class_name, 2.0)
            damage_size = width * height
            damage_severity = class_weight * damage_size * confidence
            
            weighted_score += damage_severity
            total_area += damage_size
        
        # Normalize and adjust score
        base_score = min(weighted_score * 100, 100)
        count_multiplier = min(1 + (len(detections) - 1) * 0.1, 2.0)
        area_percentage = (total_area * 100)
        area_multiplier = min(1 + area_percentage / 10, 1.5)
        
        final_score = min(base_score * count_multiplier * area_multiplier, 100)
        
        # Determine severity level
        if final_score >= 80:
            severity_level = 'Critical'
        elif final_score >= 60:
            severity_level = 'High'
        elif final_score >= 40:
            severity_level = 'Moderate'
        elif final_score >= 20:
            severity_level = 'Low'
        else:
            severity_level = 'Minimal'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(damage_types, severity_level)
        
        return {
            'severity_score': round(final_score, 2),
            'severity_level': severity_level,
            'damage_types': damage_types,
            'damage_area_percentage': round(area_percentage, 2),
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, damage_types, severity_level):
        """
        Generate maintenance recommendations
        """
        recommendations = []
        
        if 'pothole' in damage_types:
            if damage_types['pothole'] > 3:
                recommendations.append('URGENT: Multiple potholes - immediate repair required')
            else:
                recommendations.append('HIGH PRIORITY: Pothole repair needed')
        
        if any(crack in damage_types for crack in ['longitudinal_crack', 'lateral_crack']):
            total_cracks = sum(damage_types.get(crack, 0) for crack in ['longitudinal_crack', 'lateral_crack'])
            if total_cracks > 5:
                recommendations.append('MEDIUM PRIORITY: Extensive cracking - consider resurfacing')
            else:
                recommendations.append('MEDIUM PRIORITY: Crack sealing recommended')
        
        if severity_level == 'Critical':
            recommendations.append('CRITICAL: Immediate attention required')
        elif severity_level == 'High':
            recommendations.append('Schedule repairs within 1-2 weeks')
        elif severity_level == 'Moderate':
            recommendations.append('Schedule repairs within 1-2 months')
        
        return recommendations or ['Continue regular monitoring']

# Example usage
if __name__ == "__main__":
    detector = RoadDamageDetector('road_damage_model.pt', 'config.json')
    
    # Example detection
    # result = detector.detect_damage('road_image.jpg')
    # print(f"Detected {result['damage_count']} damages with severity score: {result['severity_score']}")
