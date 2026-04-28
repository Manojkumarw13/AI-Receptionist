"""
Unit tests for ML predictor
Tests model initialization and predictions
"""
import pytest
from datetime import datetime, timedelta

def test_ml_predictor_import():
    """Test ML predictor can be imported"""
    try:
        from utils.ml_predictor import appointment_predictor
        assert appointment_predictor is not None
    except ImportError as e:
        pytest.fail(f"Failed to import ML predictor: {e}")

def test_model_initialization():
    """Test ML model initializes"""
    from utils.ml_predictor import appointment_predictor
    assert appointment_predictor is not None
    assert hasattr(appointment_predictor, 'predict_availability')

def test_prediction_with_valid_data():
    """Test predictions with valid data"""
    from utils.ml_predictor import appointment_predictor
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    is_optimal, message = appointment_predictor.predict_availability(
        tomorrow, "10:00", 30
    )
    
    assert isinstance(is_optimal, bool)
    assert isinstance(message, str)
    assert len(message) > 0

def test_prediction_with_future_date():
    """Test predictions handle far future dates"""
    from utils.ml_predictor import appointment_predictor
    
    # Test with far future date (no historical data)
    future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    is_optimal, message = appointment_predictor.predict_availability(
        future_date, "10:00", 30
    )
    
    assert isinstance(is_optimal, bool)
    assert isinstance(message, str)



def test_different_durations():
    """Test predictions with different appointment durations"""
    from utils.ml_predictor import appointment_predictor
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Test 30 minute appointment
    is_optimal_30, msg_30 = appointment_predictor.predict_availability(
        tomorrow, "10:00", 30
    )
    assert isinstance(is_optimal_30, bool)
    
    # Test 60 minute appointment
    is_optimal_60, msg_60 = appointment_predictor.predict_availability(
        tomorrow, "10:00", 60
    )
    assert isinstance(is_optimal_60, bool)
