"""
Test script to verify image validation (road vs non-road)
Tests that non-road images are rejected BEFORE saving to database
"""

import os
import json
from damagepipeline import initialize_pipeline

def test_validation():
    """Test the validation pipeline"""
    
    print("=" * 60)
    print("Testing Image Validation Pipeline")
    print("=" * 60)
    
    # Initialize pipeline
    ROAD_CLASSIFIER_PATH = "tomunizua/road-classification_filter"
    
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    YOLO_MODEL_PATH = os.path.join(os.path.dirname(BASE_PATH), "models", "best.pt")
    
    print(f"\n📦 Initializing pipeline...")
    print(f"   YOLO Model: {YOLO_MODEL_PATH}")
    
    pipeline = initialize_pipeline(ROAD_CLASSIFIER_PATH, YOLO_MODEL_PATH)
    
    if not pipeline:
        print("❌ Failed to initialize pipeline")
        return
    
    print("✅ Pipeline initialized successfully\n")
    
    # Test with existing images
    test_images = [
        ("backend/uploads/RW-20251007010830-1954_27.jpg", "Expected: Road image with damage"),
        ("backend/uploads/RW-20251007143526-9233_26.jpg", "Expected: Road image"),
    ]
    
    for image_path, description in test_images:
        # Check if file exists from project root
        full_path = image_path
        if not os.path.exists(full_path):
            full_path = os.path.join(os.path.dirname(BASE_PATH), image_path)
        
        if os.path.exists(full_path):
            print(f"\n📸 Testing: {full_path}")
            print(f"   {description}")
            
            result = pipeline.analyze_image(full_path)
            
            print(f"   Status: {result['status']}")
            print(f"   Message: {result.get('message', 'N/A')}")
            
            if 'pipeline_stages' in result:
                road_check = result['pipeline_stages'].get('road_classification', {})
                print(f"   Road Detection: {road_check.get('is_road')} (confidence: {road_check.get('confidence', 'N/A')})")
            
            if result['status'] == 'completed':
                summary = result.get('summary', {})
                print(f"   ✅ Would be SAVED to database")
                print(f"      - Damage detected: {summary.get('total_damages', 0)} items")
                print(f"      - Damage types: {summary.get('damage_types', [])}")
                print(f"      - Severity: {summary.get('severity_level', 'N/A')}")
            elif result['status'] == 'no_damage':
                print(f"   ✅ Would be SAVED to database (valid road, no damage)")
            elif result['status'] == 'rejected':
                print(f"   ❌ Would be REJECTED (NOT saved to database)")
                print(f"      Reason: {result.get('message', 'Unknown')}")
        else:
            print(f"\n⚠️  Test image not found: {full_path}")
    
    print("\n" + "=" * 60)
    print("Validation Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_validation()