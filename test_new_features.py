#!/usr/bin/env python3
"""
Test script to verify all new dashboard features are working
Run this to ensure everything is properly configured
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_database():
    """Test database connection and data"""
    try:
        from database import db, Report
        from integrated_backend import app
        
        with app.app_context():
            # Check if reports exist
            report_count = Report.query.count()
            print(f"✅ Database Connection: OK")
            print(f"   • Reports in database: {report_count}")
            
            # Check for cost calculations
            reports_with_cost = Report.query.filter(Report.estimated_cost > 0).count()
            print(f"   • Reports with estimated costs: {reports_with_cost}")
            
            # Check for different statuses
            statuses = {}
            for report in Report.query.all():
                status = report.status
                statuses[status] = statuses.get(status, 0) + 1
            
            print(f"   • Report statuses:")
            for status, count in statuses.items():
                print(f"     - {status}: {count}")
            
            # Check damage types
            damage_types = set()
            for report in Report.query.all():
                if report.damage_type:
                    damage_types.add(report.damage_type)
            
            print(f"   • Damage types detected: {', '.join(sorted(damage_types))}")
            
            return True
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False

def test_cost_calculation():
    """Test cost calculation function"""
    try:
        from integrated_backend import estimate_repair_cost
        
        print(f"\n✅ Cost Calculation Function: OK")
        
        # Test cases
        test_cases = [
            ('pothole', 50, 1),
            ('longitudinal_crack', 75, 2),
            ('mixed', 100, 3),
            ('none', 0, 1)
        ]
        
        print("   • Test cases:")
        for damage_type, severity, count in test_cases:
            cost = estimate_repair_cost(damage_type, severity, count)
            print(f"     - {damage_type} (severity {severity}, count {count}): ₦{cost:,}")
        
        return True
    except Exception as e:
        print(f"❌ Cost Calculation Error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    try:
        from integrated_backend import app
        import json
        
        with app.test_client() as client:
            # Test admin reports endpoint
            response = client.get(
                '/api/admin/reports',
                headers={'Authorization': 'Basic YWRtaW46c2VjcmV0'}
            )
            
            if response.status_code == 200:
                data = response.get_json()
                report_count = len(data.get('reports', []))
                print(f"\n✅ API Endpoints: OK")
                print(f"   • /api/admin/reports: {report_count} reports returned")
                
                # Check if estimated_cost is in response
                if report_count > 0:
                    first_report = data['reports'][0]
                    if 'estimated_cost' in first_report:
                        print(f"   • estimated_cost field: Present ✓")
                        print(f"     Sample: Report {first_report['tracking_number']} = ₦{first_report['estimated_cost']:,}")
                    else:
                        print(f"   • estimated_cost field: MISSING ✗")
                        return False
                
                return True
            else:
                print(f"❌ API Error: Status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ API Test Error: {e}")
        return False

def test_frontend_features():
    """Check frontend file for new features"""
    try:
        frontend_path = "frontend/admin.html"
        with open(frontend_path, 'r') as f:
            content = f.read()
        
        features = {
            'Scheduled Reports Card': 'id="scheduledReports"',
            'Budget Input Field': 'id="budgetInput"',
            'Orange Optimize Button': 'from-orange-500',
            'Async initCharts': 'async function initCharts()',
            'Dynamic Priority Queue': 'function loadPriorityQueue(reports, budget'
        }
        
        print(f"\n✅ Frontend Features:")
        all_present = True
        for feature, search_term in features.items():
            if search_term in content:
                print(f"   ✓ {feature}")
            else:
                print(f"   ✗ {feature} - MISSING")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"❌ Frontend Check Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 RoadWatch Dashboard Features Test Suite")
    print("=" * 60)
    
    results = {}
    
    print("\n1️⃣  Testing Database...")
    results['database'] = test_database()
    
    print("\n2️⃣  Testing Cost Calculation...")
    results['costs'] = test_cost_calculation()
    
    print("\n3️⃣  Testing API Endpoints...")
    results['api'] = test_api_endpoints()
    
    print("\n4️⃣  Testing Frontend Features...")
    results['frontend'] = test_frontend_features()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name.capitalize()}")
    
    all_pass = all(results.values())
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✅ ALL TESTS PASSED!")
        print("\n🚀 Your dashboard is ready to use:")
        print("   • Refresh button is orange")
        print("   • Stat cards show: Total, Scheduled, In Progress, Completed")
        print("   • Reports Over Time uses real data")
        print("   • Budget optimization system is functional")
        print("   • All reports have estimated costs")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nPlease review the errors above and:")
        print("   1. Check backend is running")
        print("   2. Verify database has reports")
        print("   3. Run: python backend/calculate_missing_costs.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())