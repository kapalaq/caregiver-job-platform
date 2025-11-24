"""
Quick test script to verify database connection and basic setup
Run this before running the main queries.py file
"""

from sqlalchemy import create_engine, text
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'caregiver_platform',
    'user': 'root',
    'password': 'password'  # MySQL password
}

def test_connection():
    """Test database connection"""
    print("Testing database connection...")
    
    try:
        DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✓ Database connection successful!")
        return True
    
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPlease check:")
        print("1. MySQL server is running")
        print("2. Database 'caregiver_platform' exists")
        print("3. Username and password are correct")
        print("4. PyMySQL is installed: pip install PyMySQL")
        return False


def test_tables():
    """Check if all required tables exist"""
    print("\nChecking database tables...")
    
    required_tables = [
        'USER', 'CAREGIVER', 'MEMBER', 'ADDRESS', 
        'JOB', 'JOB_APPLICATION', 'APPOINTMENT'
    ]
    
    try:
        DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            existing_tables = [row[0] for row in result.fetchall()]
            
            missing_tables = []
            for table in required_tables:
                if table in existing_tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} (missing)")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\n✗ Missing tables: {', '.join(missing_tables)}")
                print("Please run: mysql -u root -p caregiver_platform < database/db_init.sql")
                return False
            else:
                print("\n✓ All required tables exist!")
                return True
    
    except Exception as e:
        print(f"✗ Error checking tables: {e}")
        return False


def test_data():
    """Check if tables have data"""
    print("\nChecking table data...")
    
    try:
        DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(DATABASE_URL)
        
        tables_to_check = {
            'USER': 10,
            'CAREGIVER': 10,
            'MEMBER': 10,
            'ADDRESS': 10,
            'JOB': 10,
            'JOB_APPLICATION': 10,
            'APPOINTMENT': 10
        }
        
        all_ok = True
        with engine.connect() as conn:
            for table, min_rows in tables_to_check.items():
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                
                if count >= min_rows:
                    print(f"  ✓ {table}: {count} rows")
                else:
                    print(f"  ✗ {table}: {count} rows (expected at least {min_rows})")
                    all_ok = False
        
        if all_ok:
            print("\n✓ All tables have sufficient data!")
            return True
        else:
            print("\n✗ Some tables need more data")
            print("Please run: mysql -u root -p caregiver_platform < database/db_init.sql")
            return False
    
    except Exception as e:
        print(f"✗ Error checking data: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("  CAREGIVER PLATFORM - DATABASE SETUP VERIFICATION")
    print("=" * 70)
    print()
    
    # Update password reminder
    if DB_CONFIG['password'] == 'your_password':
        print("⚠️  WARNING: Please update the password in this file!")
        print("   Edit the DB_CONFIG dictionary at the top of this file.\n")
    
    # Run tests
    connection_ok = test_connection()
    
    if not connection_ok:
        print("\n" + "=" * 70)
        print("  SETUP INCOMPLETE - Fix connection issues first")
        print("=" * 70)
        sys.exit(1)
    
    tables_ok = test_tables()
    
    if not tables_ok:
        print("\n" + "=" * 70)
        print("  SETUP INCOMPLETE - Initialize database first")
        print("=" * 70)
        sys.exit(1)
    
    data_ok = test_data()
    
    print("\n" + "=" * 70)
    if connection_ok and tables_ok and data_ok:
        print("  ✓ SETUP COMPLETE - Ready to run queries.py!")
    else:
        print("  ✗ SETUP INCOMPLETE - Please fix issues above")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
