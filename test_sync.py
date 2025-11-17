#!/usr/bin/env python3
"""
Test script to verify admin dashboard synchronization with backend
"""

import json
import re
import os
from pathlib import Path

def check_api_endpoints():
    """Check if all required API endpoints are implemented in backend"""
    backend_file = 'api/integrated_backend.py'
    
    # Read backend file
    with open(backend_file, 'r') as f:
        content = f.read()
    
    # Find all @app.route definitions
    routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", content)
    routes = sorted(set(routes))
    
    print("\n✓ Backend API Endpoints Found:")
    for route in routes:
        print(f"  - {route}")
    
    return routes

def check_frontend_api_calls():
    """Check what API endpoints the frontend is calling"""
    frontend_file = 'frontend/admin.js'
    
    with open(frontend_file, 'r') as f:
        content = f.read()
    
    # Find all fetch calls with API_BASE_URL
    api_calls = re.findall(
        r"fetch\(['\"]?\$\{API_BASE_URL\}([^'\"]+)['\"]?",
        content
    )
    
    # Also find direct string API calls
    api_calls += re.findall(
        r"fetch\(['\"]([^'\"]*api[^'\"]*)['\"]",
        content
    )
    
    api_calls = sorted(set(api_calls))
    
    print("\n✓ Frontend API Calls Found:")
    for call in api_calls:
        print(f"  - {call}")
    
    return api_calls

def check_severity_score_handling():
    """Check if severity_score is handled consistently"""
    frontend_file = 'frontend/admin.js'
    
    with open(frontend_file, 'r') as f:
        content = f.read()
    
    # Look for potential issues with severity_score
    issues = []
    
    # Check for "/10" suffix which suggests wrong scale
    if '/10' in content:
        matches = re.findall(r"[^'\"]*(/10)[^'\"]*", content)
        if matches:
            issues.append("⚠ Found '/10' suffix in severity display (should be 0-100)")
    
    # Check for severity_score * 100 which is correct (0-1 to 0-100)
    if '*100' in content and 'severity' in content.lower():
        print("✓ Found severity_score * 100 conversions (correct)")
    
    return issues

def check_config_loading():
    """Check if config.js is properly loaded"""
    admin_html = 'frontend/admin.html'
    
    with open(admin_html, 'r') as f:
        content = f.read()
    
    if 'config.js' in content:
        print("✓ config.js is loaded in admin.html")
        return True
    else:
        print("✗ config.js is NOT loaded in admin.html")
        return False

def main():
    print("="*60)
    print("RoadWatch Admin Dashboard Synchronization Test")
    print("="*60)
    
    # Check API endpoints
    endpoints = check_api_endpoints()
    
    # Check frontend calls
    frontend_calls = check_frontend_api_calls()
    
    # Verify critical endpoints exist
    critical_endpoints = [
        '/api/admin/login',
        '/api/admin/reports',
        '/api/admin/update-status'
    ]
    
    print("\n✓ Critical Endpoints Check:")
    all_found = True
    for endpoint in critical_endpoints:
        if endpoint in endpoints:
            print(f"  ✓ {endpoint}")
        else:
            print(f"  ✗ {endpoint} - MISSING!")
            all_found = False
    
    # Check severity score handling
    print("\n✓ Severity Score Handling:")
    severity_issues = check_severity_score_handling()
    if not severity_issues:
        print("  ✓ Severity score handling looks correct")
    else:
        for issue in severity_issues:
            print(f"  {issue}")
    
    # Check config loading
    print("\n✓ Configuration:")
    config_loaded = check_config_loading()
    
    # Summary
    print("\n" + "="*60)
    if all_found and config_loaded and not severity_issues:
        print("✓ Synchronization Check PASSED")
        print("The admin dashboard is properly synchronized with the backend.")
    else:
        print("⚠ Synchronization Check INCOMPLETE")
        print("Review the issues above.")
    print("="*60)

if __name__ == '__main__':
    main()
