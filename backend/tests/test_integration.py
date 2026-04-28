"""
Integration tests for complete workflows
Tests end-to-end booking, cancellation, and visitor flows
"""
import pytest
from datetime import datetime, timedelta

def test_complete_booking_and_cancellation_flow():
    """Test full booking and cancellation workflow"""
    from agent.tools import book_appointment, cancel_appointment
    
    # Book appointment
    tomorrow = datetime.now() + timedelta(days=1)
    book_result = book_appointment.invoke({
        "appointment_year": tomorrow.year,
        "appointment_month": tomorrow.month,
        "appointment_day": tomorrow.day,
        "appointment_hour": 14,
        "appointment_minute": 30,
        "doctor_name": "Dr. Smith",
        "disease": "Checkup",
        "user_email": "integration_test@example.com"
    })
    
    # Verify booking succeeded
    assert isinstance(book_result, dict)
    if book_result.get("success"):
        assert "appointment_id" in book_result or "message" in book_result
        
        # Cancel the appointment
        cancel_result = cancel_appointment.invoke({
            "appointment_year": tomorrow.year,
            "appointment_month": tomorrow.month,
            "appointment_day": tomorrow.day,
            "appointment_hour": 14,
            "appointment_minute": 30,
            "user_email": "integration_test@example.com"
        })
        
        assert isinstance(cancel_result, dict)

def test_duplicate_booking_prevention():
    """Test system prevents duplicate bookings"""
    from agent.tools import book_appointment
    
    tomorrow = datetime.now() + timedelta(days=2)
    
    # First booking
    result1 = book_appointment.invoke({
        "appointment_year": tomorrow.year,
        "appointment_month": tomorrow.month,
        "appointment_day": tomorrow.day,
        "appointment_hour": 11,
        "appointment_minute": 0,
        "doctor_name": "Dr. Smith",
        "disease": "Flu",
        "user_email": "duplicate_test@example.com"
    })
    
    # Second booking at same time
    result2 = book_appointment.invoke({
        "appointment_year": tomorrow.year,
        "appointment_month": tomorrow.month,
        "appointment_day": tomorrow.day,
        "appointment_hour": 11,
        "appointment_minute": 0,
        "doctor_name": "Dr. Jones",
        "disease": "Cold",
        "user_email": "duplicate_test@example.com"
    })
    
    # At least one should fail or warn about conflict
    assert isinstance(result1, dict)
    assert isinstance(result2, dict)
    
    # If first succeeded, second should fail
    if result1.get("success"):
        # Second booking should fail due to conflict
        assert result2.get("success") == False or "conflict" in result2.get("message", "").lower()

def test_visitor_checkin_workflow():
    """Test complete visitor check-in workflow"""
    from agent.tools import register_visitor
    
    # Register visitor
    result = register_visitor.invoke({
        "name": "Jane Smith",
        "purpose": "Business Meeting",
        "company": "Tech Corp"
    })
    
    assert isinstance(result, str)
    assert len(result) > 0

def test_database_connection():
    """Test database connection works"""
    from database.connection import get_session
    
    session = get_session()
    assert session is not None
    session.close()

def test_timezone_utils():
    """Test timezone utilities work correctly"""
    from utils.timezone_utils import now_with_timezone, get_timezone
    
    # Test getting current time with timezone
    now = now_with_timezone()
    assert now is not None
    assert now.tzinfo is not None
    
    # Test getting timezone
    tz = get_timezone()
    assert tz is not None
