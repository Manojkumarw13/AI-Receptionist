"""
Pydantic schemas for AI Receptionist API request/response validation.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Appointments ──────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    doctor_name: str
    disease: str
    appointment_year: int
    appointment_month: int
    appointment_day: int
    appointment_hour: int
    appointment_minute: int


class AppointmentOut(BaseModel):
    id: int
    user_email: str
    doctor_name: str
    disease: str
    appointment_time: datetime
    status: str
    qr_code_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentCancelRequest(BaseModel):
    appointment_id: int


# ── Doctors ───────────────────────────────────────────────────────────────────

class DoctorOut(BaseModel):
    id: int
    name: str
    specialty: str

    class Config:
        from_attributes = True


# ── Availability ──────────────────────────────────────────────────────────────

class AvailabilityResponse(BaseModel):
    success: bool
    appointment_time: Optional[str] = None
    message: str


# ── Visitors ──────────────────────────────────────────────────────────────────

class VisitorCreate(BaseModel):
    name: str
    purpose: str
    company: Optional[str] = None


class VisitorOut(BaseModel):
    id: int
    name: str
    purpose: str
    company: Optional[str]
    check_in_time: datetime
    image_path: Optional[str]

    class Config:
        from_attributes = True


# ── Generic response ──────────────────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
