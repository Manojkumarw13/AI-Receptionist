"""
Unit tests for database operations
Tests database connection, models, and queries
"""
import pytest

def test_database_imports():
    """Test database modules can be imported"""
    try:
        from database.connection import get_session, init_db
        from database.models import User, Appointment, Doctor, Visitor
        assert get_session is not None
        assert init_db is not None
    except ImportError as e:
        pytest.fail(f"Failed to import database modules: {e}")

def test_database_initialization():
    """Test database initializes correctly"""
    from database.connection import init_db
    
    # Should not raise any errors
    init_db()

def test_session_creation():
    """Test database session can be created"""
    from database.connection import get_session
    
    session = get_session()
    assert session is not None
    session.close()

def test_models_structure():
    """Test database models have required fields"""
    from database.models import User, Appointment, Doctor, Visitor
    
    # Test User model
    assert hasattr(User, 'email')
    assert hasattr(User, 'password_hash')
    assert hasattr(User, 'name')
    
    # Test Appointment model
    assert hasattr(Appointment, 'appointment_time')
    assert hasattr(Appointment, 'doctor_name')
    assert hasattr(Appointment, 'user_email')
    assert hasattr(Appointment, 'is_deleted')
    
    # Test Doctor model
    assert hasattr(Doctor, 'name')
    assert hasattr(Doctor, 'specialty')
    
    # Test Visitor model
    assert hasattr(Visitor, 'name')
    assert hasattr(Visitor, 'purpose')
    assert hasattr(Visitor, 'check_in_time')

def test_query_doctors():
    """Test querying doctors from database"""
    from database.connection import get_session
    from database.models import Doctor
    
    session = get_session()
    try:
        doctors = session.query(Doctor).limit(5).all()
        assert isinstance(doctors, list)
        # May be empty if database not populated
    finally:
        session.close()

def test_soft_delete_flag():
    """Test appointments have soft delete functionality"""
    from database.models import Appointment
    
    # Verify is_deleted field exists
    assert hasattr(Appointment, 'is_deleted')
