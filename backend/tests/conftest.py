import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def sample_user():
    """Create sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "Test123!@#",
        "name": "Test User"
    }

@pytest.fixture
def sample_appointment():
    """Create sample appointment data"""
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    return {
        "year": tomorrow.year,
        "month": tomorrow.month,
        "day": tomorrow.day,
        "hour": 10,
        "minute": 0,
        "doctor_name": "Dr. Smith",
        "disease": "Flu",
        "user_email": "test@example.com"
    }

@pytest.fixture
def test_db():
    """Setup test database"""
    from database.connection import init_db
    init_db()
    yield
    # Cleanup handled by database
