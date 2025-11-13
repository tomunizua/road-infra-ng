#!/usr/bin/env python3
"""
Database Migration Script: Add GPS and LGA Fields
This script safely adds the new GPS and LGA columns to existing SQLite databases.
Run this ONCE before starting the updated backend.
"""

import sqlite3
import sys
import os
from datetime import datetime

def migrate_database(db_path):
    """Add GPS and LGA columns to existing reports table"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("   It will be created automatically when you start the backend.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(reports)")
        columns = {row[1] for row in cursor.fetchall()}
        
        columns_to_add = {
            'state': 'VARCHAR(50)',
            'lga': 'VARCHAR(100)',
            'gps_latitude': 'FLOAT',
            'gps_longitude': 'FLOAT',
            'gps_detected': 'BOOLEAN'
        }
        
        any_added = False
        
        for col_name, col_type in columns_to_add.items():
            if col_name in columns:
                print(f"⏭️  Column '{col_name}' already exists, skipping...")
            else:
                print(f"➕ Adding column '{col_name}' ({col_type})...")
                
                if col_name == 'state':
                    cursor.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type} DEFAULT 'Lagos' NOT NULL")
                elif col_name == 'gps_detected':
                    cursor.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type} DEFAULT 0 NOT NULL")
                else:
                    cursor.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}")
                
                any_added = True
                print(f"   ✅ Column '{col_name}' added successfully")
        
        if any_added:
            conn.commit()
            print("\n✅ Database migration completed successfully!")
            print(f"   Updated database: {db_path}")
            return True
        else:
            print("\n✅ No migrations needed - all columns already exist")
            return True
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Run migration on all databases"""
    
    print("=" * 60)
    print("🔄 GPS & LGA Database Migration Utility")
    print("=" * 60)
    print()
    
    # Databases to migrate
    databases = [
        'road_reports.db',
        'instance/roadwatch.db',
        'instance/road_reports.db'
    ]
    
    migration_success = True
    
    for db_file in databases:
        db_path = os.path.join(os.path.dirname(__file__), db_file)
        
        if os.path.exists(db_path):
            print(f"\n📌 Migrating: {db_path}")
            if not migrate_database(db_path):
                migration_success = False
        else:
            print(f"\n⏭️  Skipping (not found): {db_path}")
    
    print("\n" + "=" * 60)
    if migration_success:
        print("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("\n📝 Next steps:")
        print("   1. Start the backend: python integrated_backend.py")
        print("   2. Test GPS detection in citizen portal")
        print("   3. Check admin dashboard for GPS/LGA data")
    else:
        print("❌ SOME MIGRATIONS FAILED - Check errors above")
        sys.exit(1)
    print("=" * 60)


if __name__ == '__main__':
    main()