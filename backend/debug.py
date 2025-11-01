#!/usr/bin/env python3
"""
RoadWatch Nigeria - Debug and Test Script
This script helps identify and fix common issues
"""

import requests
import json
import time
import sqlite3
from datetime import datetime

def test_server_connection():
    """Test if the server is running and responding"""
    print("🔍 Testing server connection...")
    
    try:
        # Test basic connection
        response = requests.get('http://localhost:5000/api/test', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            return True
        else:
            print(f"❌ Server responding with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on port 5000?")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n💚 Testing health endpoint...")
    
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Database connected: {data.get('database_connected', 'Unknown')}")
            print(f"   Pipeline loaded: {data.get('pipeline_loaded', 'Unknown')}")
            print(f"   Total reports: {data.get('total_reports', 'Unknown')}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_database():
    """Test database connection and structure"""
    print("\n🗄️  Testing database...")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('road_reports.db')
        cursor = conn.cursor()
        
        # Check if reports table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Reports table exists")
            
            # Count reports
            cursor.execute("SELECT COUNT(*) FROM reports")
            count = cursor.fetchone()[0]
            print(f"   Total reports in database: {count}")
            
            # Show recent reports
            cursor.execute("SELECT tracking_number, location, status, created_at FROM reports ORDER BY created_at DESC LIMIT 3")
            recent_reports = cursor.fetchall()
            
            if recent_reports:
                print("   Recent reports:")
                for report in recent_reports:
                    print(f"     - {report[0]}: {report[1]} ({report[2]})")
            
        else:
            print("❌ Reports table does not exist")
        
        conn.close()
        return table_exists is not None
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_submit_report():
    """Test submitting a report"""
    print("\n📝 Testing report submission...")
    
    test_data = {
        "location": "Test Location, Lagos",
        "description": "Test road damage report from debug script",
        "contact": "+234 800 TEST 123"
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/submit-report',
            headers={'Content-Type': 'application/json'},
            json=test_data,
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                tracking_number = data.get('tracking_number')
                print(f"✅ Report submitted successfully")
                print(f"   Tracking number: {tracking_number}")
                return tracking_number
            else:
                print(f"❌ Report submission failed: {data}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Report submission test failed: {e}")
        return None

def test_track_report(tracking_number):
    """Test tracking a report"""
    if not tracking_number:
        print("\n⚠️  Skipping track test - no tracking number available")
        return False
    
    print(f"\n🔍 Testing report tracking for: {tracking_number}")
    
    try:
        response = requests.get(f'http://localhost:5000/api/track/{tracking_number}', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Report tracking working")
            print(f"   Location: {data.get('location')}")
            print(f"   Status: {data.get('status')}")
            return True
        elif response.status_code == 404:
            print("❌ Report not found")
            return False
        else:
            print(f"❌ Tracking failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Report tracking test failed: {e}")
        return False

def test_admin_endpoints():
    """Test admin dashboard endpoints"""
    print("\n📊 Testing admin endpoints...")
    
    # Test reports endpoint
    try:
        response = requests.get('http://localhost:5000/api/admin/reports', timeout=10)
        if response.status_code == 200:
            data = response.json()
            reports = data.get('reports', [])
            print(f"✅ Admin reports endpoint working")
            print(f"   Found {len(reports)} reports")
        else:
            print(f"❌ Admin reports failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin reports test failed: {e}")
        return False
    
    # Test analytics endpoint
    try:
        response = requests.get('http://localhost:5000/api/admin/analytics', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin analytics endpoint working")
            print(f"   Total reports: {data.get('total_reports', 0)}")
            print(f"   Completion rate: {data.get('completion_rate', 0)}%")
        else:
            print(f"❌ Admin analytics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin analytics test failed: {e}")
        return False
    
    return True

def test_cors():
    """Test CORS configuration"""
    print("\n🌐 Testing CORS configuration...")
    
    try:
        # Test preflight request
        response = requests.options(
            'http://localhost:5000/api/submit-report',
            headers={
                'Origin': 'http://localhost:5000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        
        if response.status_code in [200, 204]:
            print("✅ CORS preflight working")
            return True
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def print_troubleshooting_tips():
    """Print troubleshooting tips based on test results"""
    print("\n" + "="*60)
    print("🛠️  TROUBLESHOOTING TIPS")
    print("="*60)
    print()
    print("📋 Common Issues and Solutions:")
    print()
    print("1. 'Failed to fetch' error:")
    print("   - Check if backend server is running")
    print("   - Make sure you're using the fixed backend")
    print("   - Check browser console for CORS errors")
    print()
    print("2. Reports not showing in admin dashboard:")
    print("   - Verify database has reports: python -c \"import sqlite3; c=sqlite3.connect('road_reports.db'); print(c.execute('SELECT COUNT(*) FROM reports').fetchone())\"")
    print("   - Check admin dashboard API calls in browser Network tab")
    print("   - Refresh the admin dashboard page")
    print()
    print("3. Tracking number disappears:")
    print("   - This is now fixed in the updated citizen portal")
    print("   - The tracking number will stay visible for 10 seconds")
    print()
    print("🚀 Quick Fixes:")
    print("   - Restart the backend server")
    print("   - Clear browser cache")
    print("   - Check browser console for errors")
    print("   - Use the fixed backend and HTML files")

def main():
    print("🛣️  RoadWatch Nigeria - Debug and Test Script")
    print("="*60)
    
    all_tests_passed = True
    
    # Run tests in order
    if not test_server_connection():
        all_tests_passed = False
        print("\n❌ Server not running. Please start the backend first:")
        print("   python fixed_backend.py")
        return
    
    if not test_health_endpoint():
        all_tests_passed = False
    
    if not test_database():
        all_tests_passed = False
    
    if not test_cors():
        all_tests_passed = False
    
    # Test report submission and tracking
    tracking_number = test_submit_report()
    if tracking_number:
        test_track_report(tracking_number)
    else:
        all_tests_passed = False
    
    if not test_admin_endpoints():
        all_tests_passed = False
    
    # Print results
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your RoadWatch system is working correctly")
        print()
        print("🌐 Access your system:")
        print("   Citizen Portal: http://localhost:5000/redo.html")
        print("   Admin Dashboard: http://localhost:5000/admin.html")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("❌ Please check the issues above")
        print_troubleshooting_tips()

if __name__ == "__main__":
    main()