"""
Database configuration and connection management for AI Receptionist.
Supports both original schema and star schema for analytics.
"""

import os
from datetime import datetime, date, time as time_type
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
# Get absolute path to project root (2 levels up from database/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_path = os.path.join(BASE_DIR, "receptionist.db")
STAR_DB_path = os.path.join(BASE_DIR, "receptionist_star.db")

DATABASE_URL = f"sqlite:///{DB_path}"
STAR_DATABASE_URL = f"sqlite:///{STAR_DB_path}"

# Create engines
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

star_engine = create_engine(
    STAR_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
StarSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=star_engine)

# Thread-safe sessions
Session = scoped_session(SessionLocal)
StarSession = scoped_session(StarSessionLocal)


def init_db():
    """Initialize the original database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def init_star_db():
    """Initialize the star schema database."""
    try:
        from models_star import Base as StarBase
        StarBase.metadata.create_all(bind=star_engine)
        logger.info("Star schema database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating star schema tables: {e}")
        return False


def get_session():
    """Get a session for the original database."""
    return Session()


def get_star_session():
    """Get a session for the star schema database."""
    return StarSession()


def close_session(session):
    """Close a database session."""
    try:
        session.close()
    except Exception as e:
        logger.error(f"Error closing session: {e}")


def check_db_exists():
    """Check if the original database file exists."""
    return os.path.exists(DB_path)


def check_star_db_exists():
    """Check if the star schema database file exists."""
    return os.path.exists(STAR_DB_path)


def get_db_stats():
    """Get statistics about the original database."""
    from .models import Base, User, Doctor, Appointment, DiseaseSpecialty, Visitor
    
    session = get_session()
    try:
        stats = {
            'users': session.query(User).count(),
            'doctors': session.query(Doctor).count(),
            'appointments': session.query(Appointment).count(),
            'disease_specialties': session.query(DiseaseSpecialty).count(),
            'visitors': session.query(Visitor).count()
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}
    finally:
        session.close()


def get_star_db_stats():
    """Get statistics about the star schema database."""
    try:
        from models_star import (
            DimDate, DimTime, DimDoctor, DimUser, DimDisease, DimVisitor,
            FactAppointment, FactVisitorCheckIn
        )
        
        session = get_star_session()
        try:
            stats = {
                'dim_date': session.query(DimDate).count(),
                'dim_time': session.query(DimTime).count(),
                'dim_doctor': session.query(DimDoctor).count(),
                'dim_user': session.query(DimUser).count(),
                'dim_disease': session.query(DimDisease).count(),
                'dim_visitor': session.query(DimVisitor).count(),
                'fact_appointments': session.query(FactAppointment).count(),
                'fact_visitor_checkins': session.query(FactVisitorCheckIn).count()
            }
            return stats
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error getting star database stats: {e}")
        return {}


# ==================== STAR SCHEMA HELPER FUNCTIONS ====================

def get_or_create_date_dimension(session, target_date):
    """
    Get or create a date dimension record.
    
    Args:
        session: Star schema database session
        target_date: datetime.date object
        
    Returns:
        DimDate: Date dimension record
    """
    from models_star import DimDate
    
    # Check if date exists
    dim_date = session.query(DimDate).filter_by(full_date=target_date).first()
    
    if not dim_date:
        # Create new date dimension
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        
        day_of_week = target_date.weekday()
        is_weekend = day_of_week >= 5
        
        dim_date = DimDate(
            full_date=target_date,
            year=target_date.year,
            quarter=(target_date.month - 1) // 3 + 1,
            month=target_date.month,
            month_name=month_names[target_date.month - 1],
            day=target_date.day,
            day_of_week=day_of_week,
            day_name=day_names[day_of_week],
            week_of_year=target_date.isocalendar()[1],
            is_weekend=is_weekend,
            is_holiday=False
        )
        session.add(dim_date)
        session.flush()
    
    return dim_date


def get_or_create_time_dimension(session, target_time):
    """
    Get or create a time dimension record.
    
    Args:
        session: Star schema database session
        target_time: datetime.time object
        
    Returns:
        DimTime: Time dimension record
    """
    from models_star import DimTime
    
    # Check if time exists
    dim_time = session.query(DimTime).filter_by(time_value=target_time).first()
    
    if not dim_time:
        # Create new time dimension
        hour = target_time.hour
        minute = target_time.minute
        
        # Calculate next time for slot
        next_minute = 30 if minute == 0 else 0
        next_hour = hour if minute == 0 else hour + 1
        
        time_slot = f"{hour:02d}:{minute:02d}-{next_hour:02d}:{next_minute:02d}"
        
        # Determine period
        if hour < 12:
            period = "Morning"
        elif hour < 17:
            period = "Afternoon"
        elif hour < 20:
            period = "Evening"
        else:
            period = "Night"
        
        is_business_hours = 9 <= hour < 18
        
        dim_time = DimTime(
            time_value=target_time,
            hour=hour,
            minute=minute,
            time_slot=time_slot,
            period=period,
            is_business_hours=is_business_hours
        )
        session.add(dim_time)
        session.flush()
    
    return dim_time


def get_doctor_by_name(session, doctor_name):
    """Get doctor dimension by name."""
    from models_star import DimDoctor
    return session.query(DimDoctor).filter_by(name=doctor_name).first()


def get_user_by_email(session, email):
    """Get user dimension by email."""
    from models_star import DimUser
    return session.query(DimUser).filter_by(email=email).first()


def get_disease_by_name(session, disease_name):
    """Get disease dimension by name."""
    from models_star import DimDisease
    return session.query(DimDisease).filter_by(disease_name=disease_name).first()


def get_visitor_by_name(session, visitor_name):
    """Get visitor dimension by name."""
    from models_star import DimVisitor
    return session.query(DimVisitor).filter_by(name=visitor_name).first()


# ==================== ANALYTICS FUNCTIONS ====================

def get_peak_appointment_hours(session, limit=10):
    """Get peak appointment hours from star schema."""
    from models_star import FactAppointment, DimTime
    
    results = session.query(
        DimTime.time_slot,
        DimTime.period,
        func.count(FactAppointment.appointment_id).label('count')
    ).join(
        FactAppointment, DimTime.time_id == FactAppointment.time_id
    ).group_by(
        DimTime.time_slot, DimTime.period
    ).order_by(
        func.count(FactAppointment.appointment_id).desc()
    ).limit(limit).all()
    
    return [{'time_slot': r.time_slot, 'period': r.period, 'count': r.count} for r in results]


def get_popular_doctors(session, limit=10):
    """Get most popular doctors from star schema."""
    from models_star import FactAppointment, DimDoctor
    
    results = session.query(
        DimDoctor.name,
        DimDoctor.specialty,
        func.count(FactAppointment.appointment_id).label('total_appointments'),
        func.avg(FactAppointment.consultation_fee).label('avg_fee'),
        DimDoctor.rating
    ).join(
        FactAppointment, DimDoctor.doctor_id == FactAppointment.doctor_id
    ).group_by(
        DimDoctor.doctor_id
    ).order_by(
        func.count(FactAppointment.appointment_id).desc()
    ).limit(limit).all()
    
    return [{
        'name': r.name,
        'specialty': r.specialty,
        'total_appointments': r.total_appointments,
        'avg_fee': round(r.avg_fee, 2) if r.avg_fee else 0,
        'rating': r.rating
    } for r in results]


def get_appointment_stats_by_status(session):
    """Get appointment statistics by status."""
    from models_star import FactAppointment
    
    results = session.query(
        FactAppointment.status,
        func.count(FactAppointment.appointment_id).label('count')
    ).group_by(
        FactAppointment.status
    ).all()
    
    return {r.status: r.count for r in results}


def get_revenue_by_specialty(session):
    """Get revenue breakdown by specialty."""
    from models_star import FactAppointment, DimDoctor
    
    results = session.query(
        DimDoctor.specialty,
        func.count(FactAppointment.appointment_id).label('total_appointments'),
        func.sum(FactAppointment.consultation_fee).label('total_revenue'),
        func.avg(FactAppointment.consultation_fee).label('avg_fee')
    ).join(
        FactAppointment, DimDoctor.doctor_id == FactAppointment.doctor_id
    ).filter(
        FactAppointment.payment_status == 'Paid'
    ).group_by(
        DimDoctor.specialty
    ).order_by(
        func.sum(FactAppointment.consultation_fee).desc()
    ).all()
    
    return [{
        'specialty': r.specialty,
        'total_appointments': r.total_appointments,
        'total_revenue': round(r.total_revenue, 2) if r.total_revenue else 0,
        'avg_fee': round(r.avg_fee, 2) if r.avg_fee else 0
    } for r in results]


if __name__ == "__main__":
    print("="*70)
    print("DATABASE INITIALIZATION")
    print("="*70)
    
    # Initialize original database
    print("\n1. Initializing original database...")
    if init_db():
        print(f"   ✓ Database initialized: {DB_path}")
        stats = get_db_stats()
        if any(stats.values()):
            print("   Statistics:")
            for table, count in stats.items():
                print(f"     - {table}: {count} records")
    else:
        print("   ✗ Failed to initialize database")
    
    # Initialize star schema database
    print("\n2. Initializing star schema database...")
    if init_star_db():
        print(f"   ✓ Star schema initialized: {STAR_DB_path}")
        stats = get_star_db_stats()
        if any(stats.values()):
            print("   Statistics:")
            for table, count in stats.items():
                print(f"     - {table}: {count} records")
    else:
        print("   ✗ Failed to initialize star schema")
    
    print("\n" + "="*70)
