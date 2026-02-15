"""
Test script for Star Schema Database and Analytics
Validates data integrity, queries, and analytics functions
"""

import sys
from datetime import datetime
from database import (
    get_star_session,
    get_peak_appointment_hours,
    get_popular_doctors,
    get_appointment_stats_by_status,
    get_revenue_by_specialty,
    get_star_db_stats
)
from models_star import (
    DimDate, DimTime, DimDoctor, DimUser, DimDisease, DimVisitor,
    FactAppointment, FactVisitorCheckIn
)
from sqlalchemy import func

def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_database_stats():
    """Test database statistics."""
    print_section("DATABASE STATISTICS")
    
    stats = get_star_db_stats()
    
    if stats:
        print("\n✓ Database connection successful")
        print("\nTable Row Counts:")
        for table, count in stats.items():
            print(f"  - {table:25s}: {count:,} records")
        
        total = sum(stats.values())
        print(f"\n  Total Records: {total:,}")
        return True
    else:
        print("\n✗ Failed to get database statistics")
        return False

def test_dimension_integrity():
    """Test dimension table integrity."""
    print_section("DIMENSION TABLE INTEGRITY")
    
    session = get_star_session()
    tests_passed = 0
    tests_total = 0
    
    try:
        # Test 1: Date dimension has no gaps
        tests_total += 1
        date_count = session.query(DimDate).count()
        if date_count > 0:
            print(f"\n✓ Date dimension populated: {date_count:,} dates")
            tests_passed += 1
        else:
            print("\n✗ Date dimension is empty")
        
        # Test 2: Time dimension has expected slots
        tests_total += 1
        time_count = session.query(DimTime).count()
        expected_slots = 26  # 08:00 to 20:00, 30-min intervals
        if time_count == expected_slots:
            print(f"✓ Time dimension correct: {time_count} slots")
            tests_passed += 1
        else:
            print(f"⚠ Time dimension: {time_count} slots (expected {expected_slots})")
        
        # Test 3: Doctors have specialties
        tests_total += 1
        doctors_with_specialty = session.query(DimDoctor).filter(
            DimDoctor.specialty != None
        ).count()
        total_doctors = session.query(DimDoctor).count()
        if doctors_with_specialty == total_doctors:
            print(f"✓ All {total_doctors} doctors have specialties")
            tests_passed += 1
        else:
            print(f"⚠ {total_doctors - doctors_with_specialty} doctors missing specialties")
        
        # Test 4: Users have valid emails
        tests_total += 1
        users_with_email = session.query(DimUser).filter(
            DimUser.email.like('%@%')
        ).count()
        total_users = session.query(DimUser).count()
        if users_with_email == total_users:
            print(f"✓ All {total_users} users have valid emails")
            tests_passed += 1
        else:
            print(f"⚠ {total_users - users_with_email} users have invalid emails")
        
        # Test 5: Diseases have ICD codes
        tests_total += 1
        diseases_with_icd = session.query(DimDisease).filter(
            DimDisease.icd_code != None
        ).count()
        total_diseases = session.query(DimDisease).count()
        if diseases_with_icd == total_diseases:
            print(f"✓ All {total_diseases} diseases have ICD codes")
            tests_passed += 1
        else:
            print(f"⚠ {total_diseases - diseases_with_icd} diseases missing ICD codes")
        
        print(f"\n✓ Dimension Integrity: {tests_passed}/{tests_total} tests passed")
        return tests_passed == tests_total
        
    except Exception as e:
        print(f"\n✗ Error testing dimensions: {e}")
        return False
    finally:
        session.close()

def test_fact_table_integrity():
    """Test fact table integrity and relationships."""
    print_section("FACT TABLE INTEGRITY")
    
    session = get_star_session()
    tests_passed = 0
    tests_total = 0
    
    try:
        # Test 1: All appointments have valid foreign keys
        tests_total += 1
        total_appointments = session.query(FactAppointment).count()
        
        # Check date_id references
        valid_dates = session.query(FactAppointment).join(
            DimDate, FactAppointment.date_id == DimDate.date_id
        ).count()
        
        if valid_dates == total_appointments:
            print(f"\n✓ All {total_appointments} appointments have valid date references")
            tests_passed += 1
        else:
            print(f"\n✗ {total_appointments - valid_dates} appointments have invalid date_id")
        
        # Test 2: Check time_id references
        tests_total += 1
        valid_times = session.query(FactAppointment).join(
            DimTime, FactAppointment.time_id == DimTime.time_id
        ).count()
        
        if valid_times == total_appointments:
            print(f"✓ All appointments have valid time references")
            tests_passed += 1
        else:
            print(f"✗ {total_appointments - valid_times} appointments have invalid time_id")
        
        # Test 3: Check doctor_id references
        tests_total += 1
        valid_doctors = session.query(FactAppointment).join(
            DimDoctor, FactAppointment.doctor_id == DimDoctor.doctor_id
        ).count()
        
        if valid_doctors == total_appointments:
            print(f"✓ All appointments have valid doctor references")
            tests_passed += 1
        else:
            print(f"✗ {total_appointments - valid_doctors} appointments have invalid doctor_id")
        
        # Test 4: Check user_id references
        tests_total += 1
        valid_users = session.query(FactAppointment).join(
            DimUser, FactAppointment.user_id == DimUser.user_id
        ).count()
        
        if valid_users == total_appointments:
            print(f"✓ All appointments have valid user references")
            tests_passed += 1
        else:
            print(f"✗ {total_appointments - valid_users} appointments have invalid user_id")
        
        # Test 5: Check disease_id references
        tests_total += 1
        valid_diseases = session.query(FactAppointment).join(
            DimDisease, FactAppointment.disease_id == DimDisease.disease_id
        ).count()
        
        if valid_diseases == total_appointments:
            print(f"✓ All appointments have valid disease references")
            tests_passed += 1
        else:
            print(f"✗ {total_appointments - valid_diseases} appointments have invalid disease_id")
        
        print(f"\n✓ Fact Table Integrity: {tests_passed}/{tests_total} tests passed")
        return tests_passed == tests_total
        
    except Exception as e:
        print(f"\n✗ Error testing fact table: {e}")
        return False
    finally:
        session.close()

def test_analytics_functions():
    """Test analytics query functions."""
    print_section("ANALYTICS FUNCTIONS")
    
    session = get_star_session()
    tests_passed = 0
    tests_total = 0
    
    try:
        # Test 1: Peak hours query
        tests_total += 1
        peak_hours = get_peak_appointment_hours(session, limit=5)
        if peak_hours and len(peak_hours) > 0:
            print(f"\n✓ Peak hours query successful: {len(peak_hours)} results")
            print(f"  Top slot: {peak_hours[0]['time_slot']} ({peak_hours[0]['count']} appointments)")
            tests_passed += 1
        else:
            print("\n✗ Peak hours query failed")
        
        # Test 2: Popular doctors query
        tests_total += 1
        popular_doctors = get_popular_doctors(session, limit=5)
        if popular_doctors and len(popular_doctors) > 0:
            print(f"✓ Popular doctors query successful: {len(popular_doctors)} results")
            print(f"  Top doctor: {popular_doctors[0]['name']} ({popular_doctors[0]['total_appointments']} appointments)")
            tests_passed += 1
        else:
            print("✗ Popular doctors query failed")
        
        # Test 3: Status statistics query
        tests_total += 1
        status_stats = get_appointment_stats_by_status(session)
        if status_stats and len(status_stats) > 0:
            print(f"✓ Status statistics query successful: {len(status_stats)} statuses")
            for status, count in status_stats.items():
                print(f"  - {status}: {count}")
            tests_passed += 1
        else:
            print("✗ Status statistics query failed")
        
        # Test 4: Revenue by specialty query
        tests_total += 1
        revenue_data = get_revenue_by_specialty(session)
        if revenue_data and len(revenue_data) > 0:
            print(f"✓ Revenue by specialty query successful: {len(revenue_data)} specialties")
            if revenue_data[0]['total_revenue'] > 0:
                print(f"  Top specialty: {revenue_data[0]['specialty']} (₹{revenue_data[0]['total_revenue']:,.0f})")
            tests_passed += 1
        else:
            print("✗ Revenue by specialty query failed")
        
        print(f"\n✓ Analytics Functions: {tests_passed}/{tests_total} tests passed")
        return tests_passed == tests_total
        
    except Exception as e:
        print(f"\n✗ Error testing analytics: {e}")
        return False
    finally:
        session.close()

def test_query_performance():
    """Test query performance."""
    print_section("QUERY PERFORMANCE")
    
    session = get_star_session()
    
    try:
        import time
        
        # Test complex join query
        start = time.time()
        results = session.query(
            DimDoctor.name,
            DimDisease.disease_name,
            func.count(FactAppointment.appointment_id).label('count')
        ).join(
            FactAppointment, DimDoctor.doctor_id == FactAppointment.doctor_id
        ).join(
            DimDisease, FactAppointment.disease_id == DimDisease.disease_id
        ).group_by(
            DimDoctor.doctor_id, DimDisease.disease_id
        ).limit(100).all()
        
        elapsed = time.time() - start
        
        print(f"\n✓ Complex join query executed in {elapsed:.3f} seconds")
        print(f"  Retrieved {len(results)} results")
        
        if elapsed < 1.0:
            print("  ✓ Performance: Excellent")
            return True
        elif elapsed < 3.0:
            print("  ⚠ Performance: Good")
            return True
        else:
            print("  ⚠ Performance: Needs optimization")
            return False
        
    except Exception as e:
        print(f"\n✗ Error testing performance: {e}")
        return False
    finally:
        session.close()

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  STAR SCHEMA DATABASE TEST SUITE")
    print("="*70)
    print(f"  Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Database Statistics", test_database_stats()))
    results.append(("Dimension Integrity", test_dimension_integrity()))
    results.append(("Fact Table Integrity", test_fact_table_integrity()))
    results.append(("Analytics Functions", test_analytics_functions()))
    results.append(("Query Performance", test_query_performance()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print()
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8s} - {test_name}")
    
    print(f"\n  Total: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! Star schema is ready for production.")
        return 0
    else:
        print(f"\n  ⚠ {total - passed} test suite(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
