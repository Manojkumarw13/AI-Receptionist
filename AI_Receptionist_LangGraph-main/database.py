"""
Database configuration and connection management for AI Receptionist.
Provides SQLAlchemy engine, session management, and initialization utilities.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file path
DATABASE_FILE = "receptionist.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create engine with connection pooling
# Using StaticPool for SQLite to handle concurrent access better
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Allow multi-threading for SQLite
    poolclass=StaticPool,
    echo=False  # Set to True for SQL query debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Thread-safe session
Session = scoped_session(SessionLocal)


def init_db():
    """
    Initialize the database by creating all tables.
    This should be called once when setting up the application.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def get_session():
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session object
        
    Usage:
        session = get_session()
        try:
            # Your database operations
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    """
    return Session()


def close_session(session):
    """
    Close a database session.
    
    Args:
        session: SQLAlchemy session to close
    """
    try:
        session.close()
    except Exception as e:
        logger.error(f"Error closing session: {e}")


def get_db():
    """
    Dependency function for getting database session with automatic cleanup.
    Useful for context managers.
    
    Yields:
        Session: SQLAlchemy session object
        
    Usage:
        with get_db() as session:
            # Your database operations
    """
    db = Session()
    try:
        yield db
    finally:
        db.close()


def check_db_exists():
    """
    Check if the database file exists.
    
    Returns:
        bool: True if database exists, False otherwise
    """
    return os.path.exists(DATABASE_FILE)


def get_db_stats():
    """
    Get statistics about the database.
    
    Returns:
        dict: Dictionary containing table counts
    """
    from models import User, Doctor, Appointment, DiseaseSpecialty, Visitor
    
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


if __name__ == "__main__":
    # Initialize database when run directly
    print("Initializing database...")
    if init_db():
        print("✓ Database initialized successfully")
        print(f"✓ Database file: {DATABASE_FILE}")
        
        # Show stats if database has data
        stats = get_db_stats()
        if any(stats.values()):
            print("\nDatabase Statistics:")
            for table, count in stats.items():
                print(f"  - {table}: {count} records")
    else:
        print("✗ Failed to initialize database")
