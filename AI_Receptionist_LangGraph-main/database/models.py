"""
Database models for AI Receptionist application.
Defines SQLAlchemy ORM models for all entities.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
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
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Create composite index for faster user-based and time-based queries
    __table_args__ = (
        Index('idx_user_time', 'user_email', 'appointment_time'),
        Index('idx_doctor_time', 'doctor_name', 'appointment_time'),
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
