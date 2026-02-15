"""
Star Schema Database Models for AI Receptionist
Dimensional modeling with fact and dimension tables for analytics
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, ForeignKey, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()


# ==================== DIMENSION TABLES ====================

class DimDate(Base):
    """Date dimension table with calendar attributes."""
    __tablename__ = 'dim_date'
    
    date_id = Column(Integer, primary_key=True, autoincrement=True)
    full_date = Column(Date, unique=True, nullable=False, index=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)  # 1-4
    month = Column(Integer, nullable=False)  # 1-12
    month_name = Column(String(20), nullable=False)
    day = Column(Integer, nullable=False)  # 1-31
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    day_name = Column(String(20), nullable=False)
    week_of_year = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    holiday_name = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_date_year_month', 'year', 'month'),
    )
    
    def __repr__(self):
        return f"<DimDate(date='{self.full_date}', day='{self.day_name}')>"


class DimTime(Base):
    """Time dimension table with time-of-day attributes."""
    __tablename__ = 'dim_time'
    
    time_id = Column(Integer, primary_key=True, autoincrement=True)
    time_value = Column(Time, unique=True, nullable=False, index=True)
    hour = Column(Integer, nullable=False)  # 0-23
    minute = Column(Integer, nullable=False)  # 0-59
    time_slot = Column(String(20), nullable=False)  # "09:00-09:30"
    period = Column(String(20), nullable=False)  # Morning/Afternoon/Evening/Night
    is_business_hours = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<DimTime(slot='{self.time_slot}', period='{self.period}')>"


class DimDoctor(Base):
    """Doctor dimension table with professional details."""
    __tablename__ = 'dim_doctor'
    
    doctor_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    specialty = Column(String(255), nullable=False, index=True)
    qualification = Column(String(255), nullable=False)
    experience_years = Column(Integer, nullable=False)
    rating = Column(Float, default=4.5)
    consultation_fee = Column(Float, nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    availability = Column(String(100), nullable=True)  # "Mon-Fri 9AM-5PM"
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_doctor_specialty_name', 'specialty', 'name'),
    )
    
    def __repr__(self):
        return f"<DimDoctor(name='{self.name}', specialty='{self.specialty}')>"


class DimUser(Base):
    """User/Patient dimension table with demographic information."""
    __tablename__ = 'dim_user'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)  # Male/Female/Other
    blood_group = Column(String(5), nullable=True)  # A+, B-, O+, etc.
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    emergency_contact = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<DimUser(name='{self.full_name}', email='{self.email}')>"


class DimDisease(Base):
    """Disease dimension table with medical classification."""
    __tablename__ = 'dim_disease'
    
    disease_id = Column(Integer, primary_key=True, autoincrement=True)
    disease_name = Column(String(255), unique=True, nullable=False, index=True)
    specialty = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # Chronic/Acute/Infectious/etc.
    severity = Column(String(50), nullable=False)  # Mild/Moderate/Severe
    description = Column(String(1000), nullable=True)
    common_symptoms = Column(String(500), nullable=True)
    icd_code = Column(String(20), nullable=True)  # International Classification of Diseases
    
    __table_args__ = (
        Index('idx_disease_specialty', 'specialty', 'disease_name'),
    )
    
    def __repr__(self):
        return f"<DimDisease(name='{self.disease_name}', specialty='{self.specialty}')>"


class DimVisitor(Base):
    """Visitor dimension table for check-in tracking."""
    __tablename__ = 'dim_visitor'
    
    visitor_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    purpose = Column(String(500), nullable=False)
    contact = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    id_type = Column(String(50), nullable=True)  # Aadhar/PAN/Driving License
    id_number = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<DimVisitor(name='{self.name}', company='{self.company}')>"


# ==================== FACT TABLE ====================

class FactAppointment(Base):
    """Fact table for appointment transactions."""
    __tablename__ = 'fact_appointments'
    
    appointment_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys to dimension tables
    date_id = Column(Integer, ForeignKey('dim_date.date_id'), nullable=False, index=True)
    time_id = Column(Integer, ForeignKey('dim_time.time_id'), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey('dim_doctor.doctor_id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('dim_user.user_id'), nullable=False, index=True)
    disease_id = Column(Integer, ForeignKey('dim_disease.disease_id'), nullable=False, index=True)
    
    # Measures (metrics)
    status = Column(String(50), nullable=False, default='Scheduled')  # Scheduled/Completed/Cancelled/No-Show
    duration_minutes = Column(Integer, default=30)
    consultation_fee = Column(Float, nullable=True)
    payment_status = Column(String(50), default='Pending')  # Pending/Paid/Refunded
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Additional attributes
    notes = Column(String(1000), nullable=True)
    prescription_id = Column(String(100), nullable=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_fact_date_doctor', 'date_id', 'doctor_id'),
        Index('idx_fact_user_date', 'user_id', 'date_id'),
        Index('idx_fact_status', 'status'),
    )
    
    # Relationships (optional, for easier querying)
    date = relationship("DimDate", backref="appointments")
    time = relationship("DimTime", backref="appointments")
    doctor = relationship("DimDoctor", backref="appointments")
    user = relationship("DimUser", backref="appointments")
    disease = relationship("DimDisease", backref="appointments")
    
    def __repr__(self):
        return f"<FactAppointment(id={self.appointment_id}, status='{self.status}')>"


# ==================== VISITOR FACT TABLE ====================

class FactVisitorCheckIn(Base):
    """Fact table for visitor check-in transactions."""
    __tablename__ = 'fact_visitor_checkins'
    
    checkin_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    date_id = Column(Integer, ForeignKey('dim_date.date_id'), nullable=False, index=True)
    time_id = Column(Integer, ForeignKey('dim_time.time_id'), nullable=False, index=True)
    visitor_id = Column(Integer, ForeignKey('dim_visitor.visitor_id'), nullable=False, index=True)
    
    # Measures
    checkout_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Timestamps
    checkin_time = Column(DateTime, default=func.now(), nullable=False)
    
    # Additional attributes
    image_path = Column(String(500), nullable=True)
    notes = Column(String(500), nullable=True)
    
    # Relationships
    date = relationship("DimDate", backref="visitor_checkins")
    time = relationship("DimTime", backref="visitor_checkins")
    visitor = relationship("DimVisitor", backref="checkins")
    
    def __repr__(self):
        return f"<FactVisitorCheckIn(id={self.checkin_id}, visitor_id={self.visitor_id})>"
