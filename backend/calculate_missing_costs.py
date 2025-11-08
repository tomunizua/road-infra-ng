#!/usr/bin/env python3
"""
Script to calculate and update estimated costs for existing reports
Run this after starting the backend to ensure all reports have costs
"""

from database import db, Report
from integrated_backend import app, estimate_repair_cost

def calculate_missing_costs():
    """Calculate estimated costs for reports that are missing them"""
    with app.app_context():
        try:
            # Get all reports
            reports = Report.query.all()
            updated_count = 0
            
            print(f"📊 Checking {len(reports)} reports for missing estimated costs...")
            
            for report in reports:
                # If estimated_cost is 0 or None, recalculate it
                if not report.estimated_cost:
                    # Calculate cost based on existing data
                    cost = estimate_repair_cost(
                        report.damage_type or 'unknown',
                        report.severity_score or 0,
                        1  # Assume 1 damage for existing reports
                    )
                    
                    report.estimated_cost = cost
                    updated_count += 1
                    
                    print(f"  ✓ {report.tracking_number}: ₦{cost:,} ({report.damage_type}, severity: {report.severity_score})")
            
            # Commit all changes
            if updated_count > 0:
                db.session.commit()
                print(f"\n✅ Updated {updated_count} reports with calculated estimated costs")
            else:
                print("\n✅ All reports already have estimated costs")
            
        except Exception as e:
            print(f"❌ Error calculating costs: {e}")
            db.session.rollback()

if __name__ == '__main__':
    calculate_missing_costs()