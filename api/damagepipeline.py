import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np
import time
import logging
import os
import gc
from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel
from huggingface_hub import hf_hub_download

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

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
        try:
            x1, y1, x2, y2 = bbox
            
            # Validate coordinates
            if x2 <= x1 or y2 <= y1:
                logger.warning(f"Invalid bbox coordinates: {bbox}. x2 <= x1 or y2 <= y1")
                return 0.001  # Return small area for invalid bbox
            
            detection_area = (x2 - x1) * (y2 - y1)
            image_area = img_width * img_height
            
            if image_area == 0:
                logger.warning(f"Image area is zero: {img_width}x{img_height}")
                return 0.001
            
            area_ratio = detection_area / image_area
            logger.debug(f"Area calculation - Detection: {detection_area:.2f}px², Image: {image_area}px², Ratio: {area_ratio:.4f}")
            
            return area_ratio
        except Exception as e:
            logger.error(f"Error calculating normalized area for bbox {bbox}, image dims {img_width}x{img_height}: {e}")
            return 0.001
    
    def calculate_detection_severity(self, detection, img_width, img_height):
        """Calculate severity score for single detection"""
        try:
            damage_type = detection['class']
            confidence = detection['confidence']
            bbox = detection['bbox']
            
            logger.debug(f"Calculating severity for {damage_type} - Confidence: {confidence:.3f}, BBox: {bbox}")
            
            if damage_type not in self.damage_weights:
                logger.warning(f"Unknown damage type: {damage_type}. Using default severity 0.5")
                return 0.5  # Default for unknown types
            
            weights = self.damage_weights[damage_type]
            area_ratio = self.calculate_normalized_area(bbox, img_width, img_height)
            
            # Severity calculation
            severity = weights['base_severity']
            logger.debug(f"  Base severity ({damage_type}): {severity:.3f}")
            
            area_contribution = area_ratio * weights['area_multiplier']
            severity += area_contribution
            logger.debug(f"  + Area contribution ({area_ratio:.4f} * {weights['area_multiplier']}): {area_contribution:.3f} = {severity:.3f}")
            
            severity *= confidence  # Scale by detection confidence
            logger.debug(f"  * Confidence {confidence:.3f} = {severity:.3f}")
            
            final_severity = min(severity, 1.0)  # Cap at 1.0
            logger.debug(f"  Final severity (capped): {final_severity:.3f}")
            
            return final_severity
        except Exception as e:
            logger.error(f"Error calculating detection severity for {detection}: {e}")
            return 0.5
    
    def calculate_image_severity(self, detections, img_width, img_height):
        """Calculate overall severity for image with multiple detections"""
        logger.info(f"Starting image severity calculation for {len(detections)} detections | Image: {img_width}x{img_height}")
        
        if not detections:
            logger.info("No detections found - returning zero severity")
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
        
        logger.info(f"Damage groups: {[(t, len(d)) for t, d in damage_groups.items()]}")
        
        # Calculate per-type severity
        type_severities = {}
        for damage_type, type_detections in damage_groups.items():
            if damage_type in self.damage_weights:
                logger.info(f"Processing {damage_type}: {len(type_detections)} detection(s)")
                weights = self.damage_weights[damage_type]
                
                # Individual severity scores
                individual_scores = [
                    self.calculate_detection_severity(det, img_width, img_height)
                    for det in type_detections
                ]
                
                logger.debug(f"  Individual scores for {damage_type}: {[f'{s:.3f}' for s in individual_scores]}")
                
                # Aggregate severity for this type
                max_individual = max(individual_scores)
                count_factor = 1 + (len(type_detections) - 1) * weights['count_penalty']
                type_severity = min(max_individual * count_factor, 1.0)
                
                logger.info(f"  {damage_type}: max_individual={max_individual:.3f}, count_factor={count_factor:.3f}, final={type_severity:.3f}")
                
                type_severities[damage_type] = {
                    'severity': type_severity,
                    'count': len(type_detections),
                    'max_individual': max_individual
                }
            else:
                logger.warning(f"Damage type '{damage_type}' not found in damage_weights")
        
        # Calculate overall severity (weighted by damage type importance)
        if type_severities:
            weighted_sum = 0
            total_weight = 0
            
            logger.info("Calculating weighted overall severity:")
            for damage_type, metrics in type_severities.items():
                # Weight by base severity and detection count
                weight = (self.damage_weights[damage_type]['base_severity'] * (1 + 0.1 * metrics['count']))
                
                contribution = metrics['severity'] * weight
                weighted_sum += contribution
                total_weight += weight
                
                logger.debug(f"  {damage_type}: severity={metrics['severity']:.3f} * weight={weight:.3f} = {contribution:.3f}")
            
            overall_severity = weighted_sum / total_weight if total_weight > 0 else 0
            logger.info(f"Overall severity: {weighted_sum:.3f} / {total_weight:.3f} = {overall_severity:.3f}")
        else:
            overall_severity = 0
            logger.warning("No valid type_severities calculated")
        
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
        
        logger.info(f"Severity classification: {severity_level} (score: {overall_severity:.3f}, thresholds: low={self.thresholds['low']}, medium={self.thresholds['medium']}, high={self.thresholds['high']})")
        
        # Find dominant damage type
        dominant_damage = max(type_severities.keys(), 
                            key=lambda x: type_severities[x]['severity']) if type_severities else None
        
        result = {
            'severity_level': severity_level,
            'severity_score': round(overall_severity, 3),
            'damage_counts': {k: v['count'] for k, v in type_severities.items()},
            'damage_severities': {k: round(v['severity'], 3) for k, v in type_severities.items()},
            'dominant_damage': dominant_damage,
            'repair_urgency': urgency,
            'total_detections': len(detections)
        }
        
        logger.info(f"Final result: {result}")
        return result

class RoadDamagePipeline:
    def __init__(self, road_classifier_path, yolo_model_path):
        """
        Initialize the complete pipeline
        
        Args:
            road_classifier_path: Path to your HuggingFace road classifier
            yolo_model_path: Path to your trained YOLO model (.pt file)
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        try:
            torch.serialization.add_safe_globals([DetectionModel])
            print("Allowed YOLO DetectionModel safe global for PyTorch 2.6+")
        except AttributeError:
            # Older PyTorch versions don't need this
            pass
        except Exception as e:
            print(f"Warning setting safe globals: {e}")

        # Initialize components
        self.road_classifier = self.load_road_classifier(road_classifier_path)
        # YOLO model is loaded from the path provided after download
        self.yolo_model = YOLO(yolo_model_path) 
        self.severity_calculator = DamageSeverityCalculator()
        
        print(f"Pipeline initialized on {self.device}")
        print(f"Road classifier loaded: {'Success' if self.road_classifier else 'Failed'}")
        print(f"YOLO model loaded: {'Success' if self.yolo_model else 'Failed'}")
    
    def load_road_classifier(self, model_path):
        """Load your road classifier from HuggingFace (Currently disabled/skipped)"""
        print(f"Road classifier (HuggingFace) is disabled - skipping load")
        return None
    
    def is_road_image(self, image_path_or_pil, threshold=0.5):
        """
        Check if image contains a road surface (Skipped if classifier is None)
        """
        if self.road_classifier is None:
            return {
                'is_road': True,  # Skip check if classifier not loaded
                'confidence': 1.0,
                'message': 'Road classifier not available - proceeding with damage detection'
            }
        # ... (rest of classification logic is skipped as per your original code's print statement)
        
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
        Detect damage using YOLO model with Low Threshold + Confidence Gating
        """
        try:
            logger.info(f"Starting YOLO damage detection on: {image_path}")
            
            # --- CONFIGURATION (TUNED FOR RECALL) ---
            # 1. Detection Threshold: Lowered to 0.25 to catch subtle cracks/potholes
            CONFIDENCE_THRESHOLD = 0.25  
            
            # 2. Gatekeeper Threshold: Required "best" score to accept the image
            # If the best detection is < 0.40, we assume the image is noise/not a road.
            GATEKEEPER_THRESHOLD = 0.40  
            # ----------------------------------------

            logger.debug(f"Using detection threshold: {CONFIDENCE_THRESHOLD}")
            
            # Run YOLO with the low threshold
            results = self.yolo_model.predict(image_path, conf=CONFIDENCE_THRESHOLD, verbose=False)
            
            # Parse results
            detections = []
            img_height, img_width = 480, 640
            max_confidence_found = 0.0 # Track the single best score in the image
            
            if len(results) > 0:
                img_height, img_width = results[0].orig_shape
                
                if len(results[0].boxes) > 0:
                    logger.info(f"Found {len(results[0].boxes)} potential detection(s)")
                    
                    for i, box in enumerate(results[0].boxes):
                        try:
                            confidence = float(box.conf[0])
                            # Track the best confidence seen so far
                            max_confidence_found = max(max_confidence_found, confidence)

                            damage_class = self.yolo_model.names[int(box.cls[0])]
                            bbox = box.xyxy[0].cpu().numpy().tolist()
                            
                            detection = {
                                'class': damage_class,
                                'confidence': confidence,
                                'bbox': bbox,
                                'center': [
                                    float((box.xyxy[0][0] + box.xyxy[0][2]) / 2),
                                    float((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                                ]
                            }
                            detections.append(detection)
                        except Exception as e:
                            logger.error(f"Error parsing detection {i}: {e}")
                            continue
                else:
                    logger.info("No detections found (boxes empty)")
            
            # --- THE GATEKEEPER LOGIC ---
            # Decision: Is this a valid road damage image?
            
            # Case A: No detections at all (even at low threshold)
            if len(detections) == 0:
                 return {
                    'detections': [],
                    'image_dimensions': [img_width, img_height],
                    'total_detections': 0,
                    'damage_types': [],
                    'status': 'rejected',
                    'message': "No road damage detected. Please ensure the image is clear."
                }

            # Case B: Detections found, but all are weak (below Gatekeeper threshold)
            if max_confidence_found < GATEKEEPER_THRESHOLD:
                logger.warning(f"GATEKEEPER REJECT: Best confidence {max_confidence_found:.2f} < {GATEKEEPER_THRESHOLD}")
                return {
                    'detections': [],
                    'image_dimensions': [img_width, img_height],
                    'total_detections': 0,
                    'damage_types': [],
                    'status': 'rejected',
                    'message': f"Image unclear (Confidence: {max_confidence_found:.0%}). The image does not appear to contain clear road damage. Please retake a closer, sharper photo."
                }

            # Case C: Valid detections found!
            result = {
                'detections': detections,
                'image_dimensions': [img_width, img_height],
                'total_detections': len(detections),
                'damage_types': list(set([d['class'] for d in detections])),
                'confidence_threshold': CONFIDENCE_THRESHOLD,
                'max_confidence': max_confidence_found,
                'status': 'valid'
            }
            
            logger.info(f"Valid damage result: {len(detections)} detections")
            return result
            
        except Exception as e:
            logger.error(f"Critical error in damage detection: {e}", exc_info=True)
            return {
                'detections': [],
                'image_dimensions': [640, 480],
                'total_detections': 0,
                'damage_types': [],
                'error': str(e),
                'status': 'error'
            }
    
    def calculate_severity(self, detections, img_width, img_height):
        """Calculate damage severity"""
        return self.severity_calculator.calculate_image_severity(
            detections, img_width, img_height
        )
    
    def analyze_image(self, image_path):
        """
        Complete pipeline analysis
        """
        analysis_start_time = time.time()
        logger.info("="*80)
        logger.info(f"PIPELINE START: Analyzing image: {image_path}")
        logger.info("="*80)
        
        result = {
            'image_path': image_path,
            'timestamp': time.time(),
            'pipeline_stages': {}
        }
        
        try:
            # Stage 1: Road Classification (Skipped or defaulted to True)
            logger.info("STAGE 1: Road Classification")
            road_result = self.is_road_image(image_path)
            result['pipeline_stages']['road_classification'] = road_result
            logger.info(f"  Result: is_road={road_result['is_road']}, confidence={road_result['confidence']:.3f}")
            
            if not road_result['is_road']:
                result['status'] = 'rejected'
                result['message'] = f"Non-road surface detected (confidence: {road_result['confidence']:.1%})"
                logger.warning(f"REJECTED: {result['message']}")
                gc.collect() # Force memory cleanup
                return result
            
            # Stage 2: Damage Detection
            logger.info("STAGE 2: Damage Detection")
            damage_result = self.detect_damage(image_path)
            result['pipeline_stages']['damage_detection'] = damage_result
            logger.info(f"  Found {damage_result['total_detections']} damage detection(s)")
            logger.info(f"  Damage types: {damage_result['damage_types']}")
            
            if damage_result['total_detections'] == 0:
                result['status'] = 'no_damage'
                result['message'] = "No road damage detected"
                result['severity_assessment'] = {
                    'severity_level': 'none',
                    'severity_score': 0.0,
                    'repair_urgency': 'none'
                }
                logger.info("NO DAMAGE: Ending pipeline")
                gc.collect() # Force memory cleanup
                return result
            
            # Stage 3: Severity Assessment
            logger.info("STAGE 3: Severity Assessment")
            severity_result = self.calculate_severity(
                damage_result['detections'],
                damage_result['image_dimensions'][0],
                damage_result['image_dimensions'][1]
            )
            result['pipeline_stages']['severity_assessment'] = severity_result
            logger.info(f"  Severity Level: {severity_result['severity_level']}")
            logger.info(f"  Severity Score: {severity_result['severity_score']}")
            logger.info(f"  Repair Urgency: {severity_result['repair_urgency']}")
            
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
            
            logger.info("="*80)
            logger.info(f"PIPELINE COMPLETE: Status=COMPLETED | Score={severity_result['severity_score']} | Time={result['processing_time']}")
            logger.info("="*80)
            gc.collect() # Force memory cleanup
            return result
            
        except Exception as e:
            logger.error(f"PIPELINE ERROR: {str(e)}", exc_info=True)
            result['status'] = 'error'
            result['message'] = f"Pipeline error: {str(e)}"
            gc.collect() # Force memory cleanup
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
    """
    Initialize the complete road damage analysis pipeline.
    
    This function handles the model download from Hugging Face Hub.
    """
    # Configuration for Hugging Face download
    HF_REPO_ID = "tomunizua/yolov8-41.7"
    HF_FILENAME = "best.pt"
    LOCAL_YOLO_PATH = os.path.join("/tmp", HF_FILENAME) # /tmp is the writable directory on Render

    try:
        # Step 1: Download the YOLO model if it's not already cached
        if not os.path.exists(LOCAL_YOLO_PATH):
            print(f"Downloading {HF_FILENAME} from Hugging Face Hub ({HF_REPO_ID})...")
            
            downloaded_file_path = hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=HF_FILENAME,
                local_dir="/tmp", # Download directly to the temporary directory
                local_dir_use_symlinks=False
            )
            yolo_model_path = downloaded_file_path
            print(f"Model successfully downloaded and saved to: {yolo_model_path}")
        else:
            yolo_model_path = LOCAL_YOLO_PATH
            print("Model found in /tmp cache. Skipping download.")
            
        # Step 2: Initialize the Pipeline with the downloaded path
        if road_classifier_path is None:
            # Assuming the road classifier is the generic placeholder if not specified
            road_classifier_path = "tomunizua/road-classification_filter" 
        
        print("Initializing Road Damage Analysis Pipeline...")
        print(f"YOLO Model Path: {yolo_model_path}")
        
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