#!/usr/bin/env python
import os
import sys
import glob

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from integrated_backend import pipeline

# Find a test image
test_images = glob.glob("uploads/*.jpg")
if test_images:
    test_image = test_images[0]
    print(f"Testing analysis with: {os.path.basename(test_image)}\n")
    
    result = pipeline.analyze_image(test_image)
    print(f"Status: {result['status']}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    if 'summary' in result:
        print(f"\n✅ Analysis Results:")
        print(f"   Severity: {result['summary']['severity_level']}")
        print(f"   Severity Score: {result['summary']['severity_score']}")
        print(f"   Damages Found: {result['summary']['total_damages']}")
        print(f"   Damage Types: {result['summary']['damage_types']}")
        print(f"   Repair Urgency: {result['summary']['repair_urgency']}")
else:
    print("❌ No test images found in uploads/")