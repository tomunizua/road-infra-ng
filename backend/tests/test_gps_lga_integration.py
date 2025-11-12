#!/usr/bin/env python3
"""
Integration Test: GPS & LGA Backend
Tests all GPS and LGA functionality to ensure proper backend integration.
Run this AFTER starting the backend: python integrated_backend.py
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5000"
API_SUBMIT = f"{BASE_URL}/api/submit-report"
API_TRACK = f"{BASE_URL}/api/track"
API_ADMIN = f"{BASE_URL}/api/admin/reports"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}🧪 TEST: {name}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.YELLOW}ℹ️  {msg}{Colors.RESET}")

def check_backend():
    """Check if backend is running"""
    print_test("Backend Connection")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/reports", timeout=2)
        if response.status_code in [200, 401]:
            print_success("Backend is running and accessible")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend - is it running?")
        print_info("Start backend with: python integrated_backend.py")
        return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def test_submit_with_gps():
    """Test report submission with GPS coordinates"""
    print_test("Submit Report WITH GPS Coordinates")
    
    payload = {
        "location": "Test GPS Location - Falomo Bridge, Lagos Island",
        "description": "Test pothole for GPS integration testing",
        "contact": "+2348012345678",
        "lga": "Lagos Island",
        "state": "Lagos",
        "gps_coordinates": {
            "latitude": 6.4613,
            "longitude": 3.4320
        }
    }
    
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_SUBMIT, json=payload, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and data.get('success'):
            tracking_num = data.get('tracking_number')
            print_success(f"Report submitted successfully!")
            print_success(f"Tracking Number: {tracking_num}")
            return tracking_num
        else:
            print_error(f"Submission failed: {data.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print_error(f"Exception during submission: {e}")
        return None

def test_submit_without_gps():
    """Test report submission without GPS (manual LGA)"""
    print_test("Submit Report WITHOUT GPS (Manual LGA)")
    
    payload = {
        "location": "Test Manual Location - CMS Road, Lekki Phase 1",
        "description": "Test cracks for manual LGA selection testing",
        "contact": "+2348098765432",
        "lga": "Lekki"
    }
    
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_SUBMIT, json=payload, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and data.get('success'):
            tracking_num = data.get('tracking_number')
            print_success(f"Report submitted successfully!")
            print_success(f"Tracking Number: {tracking_num}")
            return tracking_num
        else:
            print_error(f"Submission failed: {data.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print_error(f"Exception during submission: {e}")
        return None

def test_missing_lga():
    """Test that LGA is required"""
    print_test("Validation: Missing LGA Field")
    
    payload = {
        "location": "Test Location",
        "description": "Test description"
    }
    
    print_info("Submitting without LGA field...")
    
    try:
        response = requests.post(API_SUBMIT, json=payload, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        data = response.json()
        
        if response.status_code == 400 and 'lga' in str(data.get('error', '')):
            print_success("✓ LGA validation working - correctly rejected missing LGA")
            return True
        else:
            print_error(f"Expected 400 with LGA error, got: {response.status_code} - {data}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_track_report(tracking_num):
    """Test tracking endpoint with new fields"""
    print_test(f"Track Report: {tracking_num}")
    
    try:
        response = requests.get(f"{API_TRACK}/{tracking_num}", timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            # Check for new fields
            required_fields = ['state', 'lga', 'gps_detected']
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                print_error(f"Missing fields: {missing}")
                return False
            
            print_success(f"✓ All GPS/LGA fields present")
            print_success(f"  - State: {data.get('state')}")
            print_success(f"  - LGA: {data.get('lga')}")
            print_success(f"  - GPS Detected: {data.get('gps_detected')}")
            
            return True
        else:
            print_error(f"Tracking failed: {data}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def test_admin_reports():
    """Test admin endpoint includes new fields"""
    print_test("Admin Reports Endpoint")
    
    try:
        response = requests.get(API_ADMIN, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        data = response.json()
        
        if response.status_code == 200:
            reports = data.get('reports', [])
            print_success(f"✓ Retrieved {len(reports)} reports")
            
            if reports:
                first_report = reports[0]
                print_info(f"\nFirst Report: {first_report.get('tracking_number')}")
                
                # Check for new fields
                required_fields = ['state', 'lga', 'gps_detected', 'gps_latitude', 'gps_longitude']
                missing = [f for f in required_fields if f not in first_report]
                
                if missing:
                    print_error(f"Missing fields: {missing}")
                    return False
                
                print_success(f"✓ All GPS/LGA fields present in admin response")
                print_success(f"  - State: {first_report.get('state')}")
                print_success(f"  - LGA: {first_report.get('lga')}")
                print_success(f"  - GPS Detected: {first_report.get('gps_detected')}")
                print_success(f"  - GPS Lat: {first_report.get('gps_latitude')}")
                print_success(f"  - GPS Lon: {first_report.get('gps_longitude')}")
                
                return True
            else:
                print_info("No reports in database yet (this is OK)")
                return True
        else:
            print_error(f"Admin endpoint failed: {data}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "GPS & LGA Backend Integration Tests" + " "*9 + "║")
    print("╚" + "═"*58 + "╝")
    print(Colors.RESET)
    
    # Check backend
    if not check_backend():
        print_error("\n❌ Backend not running - cannot continue")
        print_info("Start with: python integrated_backend.py")
        sys.exit(1)
    
    results = {}
    
    # Run tests
    results['Missing LGA Validation'] = test_missing_lga()
    
    tracking_gps = test_submit_with_gps()
    results['Submit with GPS'] = tracking_gps is not None
    
    tracking_manual = test_submit_without_gps()
    results['Submit without GPS'] = tracking_manual is not None
    
    if tracking_gps:
        results['Track GPS Report'] = test_track_report(tracking_gps)
    
    if tracking_manual:
        results['Track Manual Report'] = test_track_report(tracking_manual)
    
    results['Admin Reports'] = test_admin_reports()
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{status} - {test_name}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! Backend integration is complete.{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  {passed}/{total} tests passed{Colors.RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())