"""
Database models for AI Receptionist application.
Defines SQLAlchemy ORM models for all entities.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean  # FIXED: Added Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship  # FIXED Issue #34: Added relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(email='{self.email}')>"


class Doctor(Base):
    """Doctor model for medical professionals."""
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255), nullable=False, index=True)
    
    # Create composite index for faster specialty-based lookups
    __table_args__ = (
        Index('idx_specialty_name', 'specialty', 'name'),
    )
    
    def __repr__(self):
        return f"<Doctor(name='{self.name}', specialty='{self.specialty}')>"


class Appointment(Base):
    """Appointment model for booking records."""
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey('users.email'), nullable=False, index=True)
    doctor_name = Column(String(255), nullable=False)
    disease = Column(String(255), nullable=False)
    appointment_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default='Scheduled', nullable=False)  # FIXED Issue #36: Added status field
    is_deleted = Column(Boolean, default=False, nullable=False)  # FIXED Issue #33: Soft delete support
    qr_code_path = Column(String(500), nullable=True)  # FIXED Issue #35: Track QR codes
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Track updates
    
    # Create composite index for faster user-based and time-based queries
    # FIXED Issue #18: Added standalone time index for better performance
    __table_args__ = (
        Index('idx_user_time', 'user_email', 'appointment_time'),
        Index('idx_doctor_time', 'doctor_name', 'appointment_time'),
        Index('idx_appointment_time', 'appointment_time'),  # Standalone time index
        Index('idx_status', 'status'),  # Index for status queries
    )
    
    def __repr__(self):
        return f"<Appointment(user='{self.user_email}', doctor='{self.doctor_name}', time='{self.appointment_time}')>"


class DiseaseSpecialty(Base):
    """Disease to specialty mapping model."""
    __tablename__ = 'disease_specialties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    disease = Column(String(255), unique=True, nullable=False, index=True)
    specialty = Column(String(255), nullable=False)
    
    def __repr__(self):
        return f"<DiseaseSpecialty(disease='{self.disease}', specialty='{self.specialty}')>"


class Visitor(Base):
    """Visitor check-in model."""
    __tablename__ = 'visitors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    purpose = Column(String(500), nullable=False)
    company = Column(String(255), nullable=True)
    check_in_time = Column(DateTime, default=func.now(), nullable=False, index=True)
    image_path = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<Visitor(name='{self.name}', purpose='{self.purpose}', time='{self.check_in_time}')>"
