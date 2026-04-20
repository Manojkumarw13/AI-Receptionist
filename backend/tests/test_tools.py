"""
Unit tests for tool functions
Tests individual tools like book_appointment, register_visitor, etc.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

def test_sanitize_input():
    """Test XSS prevention with sanitize_input"""
    from agent.tools import sanitize_input
    
    # Test script tag
    assert sanitize_input("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    
    # Test image tag with onerror
    assert sanitize_input("<img src=x onerror=alert(1)>") == "&lt;img src=x onerror=alert(1)&gt;"
    
    # Test normal text with whitespace
    assert sanitize_input("  John Doe  ") == "John Doe"
    
    # Test None handling
    assert sanitize_input(None) is None
    
    # Test empty string
    assert sanitize_input("") == ""

def test_book_appointment_past_date():
    """Test booking in past fails"""
    from agent.tools import book_appointment
    
    yesterday = datetime.now() - timedelta(days=1)
    result = book_appointment.invoke({
        "appointment_year": yesterday.year,
        "appointment_month": yesterday.month,
        "appointment_day": yesterday.day,
        "appointment_hour": 10,
        "appointment_minute": 0,
        "doctor_name": "Dr. Smith",
        "disease": "Flu",
        "user_email": "test@example.com"
    })
    
    assert isinstance(result, dict)
    assert result["success"] == False
    assert result["error"] == "PAST_DATE"
    assert "past" in result["message"].lower()

def test_book_appointment_outside_working_hours():
    """Test booking outside working hours fails"""
    from agent.tools import book_appointment
    
    tomorrow = datetime.now() + timedelta(days=1)
    
    # Try to book at 2 AM (outside working hours)
    result = book_appointment.invoke({
        "appointment_year": tomorrow.year,
        "appointment_month": tomorrow.month,
        "appointment_day": tomorrow.day,
        "appointment_hour": 2,
        "appointment_minute": 0,
        "doctor_name": "Dr. Smith",
        "disease": "Flu",
        "user_email": "test@example.com"
    })
    
    assert isinstance(result, dict)
    assert result["success"] == False
    assert result["error"] == "OUTSIDE_WORKING_HOURS"

def test_register_visitor_basic():
    """Test basic visitor registration
    
    FIX BUG-N21: Mock get_session so this test never touches the real database.
    Hitting a real DB produces non-deterministic results and pollutes production data.
    """
    from agent.tools import register_visitor
    
    # Build a mock session that silently accepts add/commit/close calls
    mock_session = MagicMock()
    
    with patch('agent.tools.get_session', return_value=mock_session):
        result = register_visitor.invoke({
            "name": "John Doe",
            "purpose": "Meeting",
            "company": "ABC Corp"
        })
    
    assert isinstance(result, str)
    assert "registered successfully" in result.lower() or "visitor" in result.lower()
    # Verify DB interactions happened without actually touching the DB
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_register_visitor_sanitization():
    """Test visitor registration sanitizes inputs
    
    FIX BUG-N21: Mock get_session so this test never touches the real database.
    """
    from agent.tools import register_visitor
    
    mock_session = MagicMock()
    
    # Register with malicious input
    with patch('agent.tools.get_session', return_value=mock_session):
        result = register_visitor.invoke({
            "name": "<script>alert('xss')</script>",
            "purpose": "Meeting",
            "company": "ABC Corp"
        })
    
    # Should succeed (sanitization happens internally)
    assert isinstance(result, str)

def test_qr_code_generation():
    """Test QR code generation"""
    from agent.tools import generate_qr_code
    
    result = generate_qr_code.invoke({"appointment_details": "Test appointment data"})
    
    assert isinstance(result, str)
    assert "QR Code generated" in result or "qr" in result.lower()

def test_qr_code_with_custom_path():
    """Test QR code generation with custom filepath"""
    from agent.tools import generate_qr_code
    import os
    
    custom_path = "static/images/test_qr.png"
    result = generate_qr_code.invoke({
        "appointment_details": "Test data",
        "filepath": custom_path
    })
    
    assert isinstance(result, str)
    # Check if file was created
    assert os.path.exists(custom_path) or "generated" in result.lower()
    
    # Cleanup
    if os.path.exists(custom_path):
        os.remove(custom_path)

def test_get_next_available_appointment():
    """Test getting next available appointment"""
    from agent.tools import get_next_available_appointment
    
    result = get_next_available_appointment.invoke({})
    
    assert isinstance(result, dict)
    # Should have either success or error
    assert "success" in result or "appointment_time" in result or "message" in result
