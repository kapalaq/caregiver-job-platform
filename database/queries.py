"""
Caregiver Job Platform - Database Queries
Part 2: SQL Queries using SQLAlchemy
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Database connection configuration
# Update these values according to your MySQL setup
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'caregiver_platform',
    'user': 'root',
    'password': 'password'  # MySQL password
}

# Create database connection string
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create session
Session = sessionmaker(bind=engine)
session = Session()


def print_separator(title):
    """Print a formatted separator for better output readability"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def execute_query(query, description):
    """Execute a query and print results"""
    print_separator(description)
    print(f"SQL Query:\n{query}\n")
    
    try:
        result = session.execute(text(query))
        
        # Check if it's a SELECT query
        if query.strip().upper().startswith('SELECT'):
            rows = result.fetchall()
            if rows:
                # Print column headers
                print(f"Found {len(rows)} result(s):\n")
                for i, row in enumerate(rows, 1):
                    print(f"Row {i}: {row}")
            else:
                print("No results found.")
        else:
            # For INSERT, UPDATE, DELETE
            session.commit()
            print(f"Query executed successfully. Rows affected: {result.rowcount}")
    
    except Exception as e:
        session.rollback()
        print(f"Error executing query: {e}")
    
    print("\n")


# ============================================================================
# 3. UPDATE SQL STATEMENTS
# ============================================================================

def update_queries():
    """Execute all UPDATE queries"""
    
    # 3.1 Update the phone number of Arman Armanov to +77773414141
    query_3_1 = """
    UPDATE USER 
    SET phone_number = '77773414141' 
    WHERE given_name = 'Arman' AND surname = 'Armanov'
    """
    execute_query(query_3_1, "3.1 - Update phone number of Arman Armanov")
    
    # 3.2 Add commission fee to Caregivers' hourly rate
    # $0.3 if rate < $10, otherwise 10%
    query_3_2a = """
    UPDATE CAREGIVER 
    SET hourly_rate = hourly_rate + 0.3 
    WHERE hourly_rate < 10
    """
    execute_query(query_3_2a, "3.2a - Add $0.3 commission to caregivers with hourly rate < $10")
    
    query_3_2b = """
    UPDATE CAREGIVER 
    SET hourly_rate = hourly_rate * 1.10 
    WHERE hourly_rate >= 10
    """
    execute_query(query_3_2b, "3.2b - Add 10% commission to caregivers with hourly rate >= $10")


# ============================================================================
# 4. DELETE SQL STATEMENTS
# ============================================================================

def delete_queries():
    """Execute all DELETE queries"""
    
    # 4.1 Delete the jobs posted by Amina Aminova
    query_4_1 = """
    DELETE FROM JOB 
    WHERE member_user_id IN (
        SELECT member_user_id 
        FROM MEMBER 
        WHERE member_user_id IN (
            SELECT user_id 
            FROM USER 
            WHERE given_name = 'Amina' AND surname = 'Aminova'
        )
    )
    """
    execute_query(query_4_1, "4.1 - Delete jobs posted by Amina Aminova")
    
    # 4.2 Delete all members who live on Kabanbay Batyr street
    query_4_2 = """
    DELETE FROM USER 
    WHERE user_id IN (
        SELECT member_user_id 
        FROM ADDRESS 
        WHERE street = 'Kabanbay Batyr'
    )
    """
    execute_query(query_4_2, "4.2 - Delete members who live on Kabanbay Batyr street")


# ============================================================================
# 5. SIMPLE QUERIES
# ============================================================================

def simple_queries():
    """Execute all simple queries"""
    
    # 5.1 Select caregiver and member names for the accepted appointments
    query_5_1 = """
    SELECT 
        uc.given_name AS caregiver_name,
        uc.surname AS caregiver_surname,
        um.given_name AS member_name,
        um.surname AS member_surname,
        a.appointment_date,
        a.appointment_time
    FROM APPOINTMENT a
    JOIN USER uc ON a.caregiver_user_id = uc.user_id
    JOIN USER um ON a.member_user_id = um.user_id
    WHERE a.status = 'confirmed'
    """
    execute_query(query_5_1, "5.1 - Caregiver and member names for confirmed appointments")
    
    # 5.2 List job ids that contain 'soft-spoken' in their other requirements
    query_5_2 = """
    SELECT job_id, other_requirements
    FROM JOB
    WHERE other_requirements LIKE '%soft-spoken%'
    """
    execute_query(query_5_2, "5.2 - Job IDs containing 'soft-spoken' in requirements")
    
    # 5.3 List the work hours of all babysitter positions
    query_5_3 = """
    SELECT 
        a.appointment_id,
        a.work_hours,
        a.appointment_date,
        u.given_name,
        u.surname
    FROM APPOINTMENT a
    JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN USER u ON c.caregiver_user_id = u.user_id
    WHERE c.caregiving_type = 'babysitter'
    """
    execute_query(query_5_3, "5.3 - Work hours of all babysitter positions")
    
    # 5.4 List the members who are looking for Elderly Care in Astana and have "No pets." rule
    query_5_4 = """
    SELECT 
        u.given_name,
        u.surname,
        u.city,
        m.house_rules,
        j.required_caregiving_type
    FROM USER u
    JOIN MEMBER m ON u.user_id = m.member_user_id
    JOIN JOB j ON m.member_user_id = j.member_user_id
    WHERE u.city = 'Astana' 
        AND j.required_caregiving_type = 'caregiver for elderly'
        AND m.house_rules LIKE '%No pets%'
    """
    execute_query(query_5_4, "5.4 - Members looking for Elderly Care in Astana with 'No pets' rule")


# ============================================================================
# 6. COMPLEX QUERIES
# ============================================================================

def complex_queries():
    """Execute all complex queries"""
    
    # 6.1 Count the number of applicants for each job posted by a member
    query_6_1 = """
    SELECT 
        j.job_id,
        u.given_name AS member_name,
        u.surname AS member_surname,
        j.required_caregiving_type,
        COUNT(ja.caregiver_user_id) AS applicant_count
    FROM JOB j
    JOIN MEMBER m ON j.member_user_id = m.member_user_id
    JOIN USER u ON m.member_user_id = u.user_id
    LEFT JOIN JOB_APPLICATION ja ON j.job_id = ja.job_id
    GROUP BY j.job_id, u.given_name, u.surname, j.required_caregiving_type
    ORDER BY applicant_count DESC
    """
    execute_query(query_6_1, "6.1 - Count applicants for each job (multiple joins with aggregation)")
    
    # 6.2 Total hours spent by caregivers for all accepted appointments
    query_6_2 = """
    SELECT 
        u.given_name,
        u.surname,
        c.caregiving_type,
        SUM(a.work_hours) AS total_work_hours
    FROM APPOINTMENT a
    JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN USER u ON c.caregiver_user_id = u.user_id
    WHERE a.status = 'confirmed'
    GROUP BY u.given_name, u.surname, c.caregiving_type
    ORDER BY total_work_hours DESC
    """
    execute_query(query_6_2, "6.2 - Total hours spent by caregivers for confirmed appointments")
    
    # 6.3 Average pay of caregivers based on accepted appointments
    query_6_3 = """
    SELECT 
        u.given_name,
        u.surname,
        c.caregiving_type,
        c.hourly_rate,
        AVG(a.total_cost) AS avg_appointment_cost,
        COUNT(a.appointment_id) AS appointment_count
    FROM APPOINTMENT a
    JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN USER u ON c.caregiver_user_id = u.user_id
    WHERE a.status = 'confirmed'
    GROUP BY u.given_name, u.surname, c.caregiving_type, c.hourly_rate
    ORDER BY avg_appointment_cost DESC
    """
    execute_query(query_6_3, "6.3 - Average pay of caregivers based on confirmed appointments")
    
    # 6.4 Caregivers who earn above average based on accepted appointments
    query_6_4 = """
    SELECT 
        u.given_name,
        u.surname,
        c.caregiving_type,
        SUM(a.total_cost) AS total_earnings
    FROM APPOINTMENT a
    JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN USER u ON c.caregiver_user_id = u.user_id
    WHERE a.status = 'confirmed'
    GROUP BY u.given_name, u.surname, c.caregiving_type
    HAVING SUM(a.total_cost) > (
        SELECT AVG(total_earnings)
        FROM (
            SELECT SUM(total_cost) AS total_earnings
            FROM APPOINTMENT
            WHERE status = 'confirmed'
            GROUP BY caregiver_user_id
        ) AS earnings_table
    )
    ORDER BY total_earnings DESC
    """
    execute_query(query_6_4, "6.4 - Caregivers earning above average (nested query)")


# ============================================================================
# 7. QUERY WITH DERIVED ATTRIBUTE
# ============================================================================

def derived_attribute_query():
    """Execute query with derived attribute"""
    
    # 7. Calculate the total cost to pay for a caregiver for all accepted appointments
    query_7 = """
    SELECT 
        u.given_name,
        u.surname,
        c.caregiving_type,
        c.hourly_rate,
        SUM(a.work_hours) AS total_work_hours,
        SUM(a.total_cost) AS total_cost_to_pay
    FROM APPOINTMENT a
    JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN USER u ON c.caregiver_user_id = u.user_id
    WHERE a.status = 'confirmed'
    GROUP BY u.given_name, u.surname, c.caregiving_type, c.hourly_rate
    ORDER BY total_cost_to_pay DESC
    """
    execute_query(query_7, "7. Total cost to pay for caregivers (derived attribute)")


# ============================================================================
# 8. VIEW OPERATION
# ============================================================================

def view_operation():
    """Execute view operation"""
    
    # First, create the view
    create_view_query = """
    CREATE OR REPLACE VIEW vw_job_applications_with_applicants AS
    SELECT 
        ja.application_id,
        ja.job_id,
        ja.date_applied,
        ja.application_status,
        ja.cover_letter,
        j.required_caregiving_type,
        j.other_requirements,
        j.date_posted,
        uc.given_name AS caregiver_name,
        uc.surname AS caregiver_surname,
        uc.email AS caregiver_email,
        uc.phone_number AS caregiver_phone,
        c.caregiving_type,
        c.hourly_rate,
        c.rating,
        um.given_name AS member_name,
        um.surname AS member_surname,
        um.email AS member_email
    FROM JOB_APPLICATION ja
    JOIN JOB j ON ja.job_id = j.job_id
    JOIN CAREGIVER c ON ja.caregiver_user_id = c.caregiver_user_id
    JOIN USER uc ON c.caregiver_user_id = uc.user_id
    JOIN MEMBER m ON j.member_user_id = m.member_user_id
    JOIN USER um ON m.member_user_id = um.user_id
    """
    execute_query(create_view_query, "8. Create View - Job applications with applicants")
    
    # Now query the view
    query_view = """
    SELECT 
        application_id,
        job_id,
        caregiver_name,
        caregiver_surname,
        caregiving_type,
        hourly_rate,
        rating,
        member_name,
        member_surname,
        application_status,
        date_applied
    FROM vw_job_applications_with_applicants
    ORDER BY date_applied DESC
    """
    execute_query(query_view, "8. Query View - All job applications and applicants")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function to execute all queries"""
    
    print("\n")
    print("*" * 80)
    print("  CAREGIVER JOB PLATFORM - PART 2: SQL QUERIES")
    print("*" * 80)
    print("\n")
    
    try:
        # Test connection
        print("Testing database connection...")
        session.execute(text("SELECT 1"))
        print("✓ Database connection successful!\n")
        
        # Execute all query sections
        
        print("\n" + "#" * 80)
        print("#  SECTION 3: UPDATE QUERIES")
        print("#" * 80)
        update_queries()
        
        print("\n" + "#" * 80)
        print("#  SECTION 4: DELETE QUERIES")
        print("#" * 80)
        delete_queries()
        
        print("\n" + "#" * 80)
        print("#  SECTION 5: SIMPLE QUERIES")
        print("#" * 80)
        simple_queries()
        
        print("\n" + "#" * 80)
        print("#  SECTION 6: COMPLEX QUERIES")
        print("#" * 80)
        complex_queries()
        
        print("\n" + "#" * 80)
        print("#  SECTION 7: QUERY WITH DERIVED ATTRIBUTE")
        print("#" * 80)
        derived_attribute_query()
        
        print("\n" + "#" * 80)
        print("#  SECTION 8: VIEW OPERATION")
        print("#" * 80)
        view_operation()
        
        print("\n" + "*" * 80)
        print("  ALL QUERIES COMPLETED SUCCESSFULLY!")
        print("*" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
    
    finally:
        session.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()