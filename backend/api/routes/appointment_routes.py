"""
Appointment routes: book, list, cancel.
All endpoints require authentication via JWT.
Uses lazy imports of agent tools to avoid native module crashes at startup.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from database.models import User, Appointment
from api.schemas import AppointmentCreate, AppointmentOut
from api.auth import get_db, get_current_user

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("", status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Book a new appointment for the current user."""
    from agent.tools import book_appointment  # lazy import
    result = book_appointment.invoke({
        "appointment_year": payload.appointment_year,
        "appointment_month": payload.appointment_month,
        "appointment_day": payload.appointment_day,
        "appointment_hour": payload.appointment_hour,
        "appointment_minute": payload.appointment_minute,
        "doctor_name": payload.doctor_name,
        "disease": payload.disease,
        "user_email": current_user.email,
    })
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Booking failed"))
    return result


@router.get("", response_model=List[AppointmentOut])
def list_appointments(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """List all upcoming (non-deleted) appointments for the current user."""
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.user_email == current_user.email,
            Appointment.is_deleted == False,
        )
        .order_by(Appointment.appointment_time.asc())
        .all()
    )
    return appointments


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Cancel (soft-delete) an appointment by its ID."""
    from agent.tools import cancel_appointment  # lazy import
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.user_email == current_user.email,
            Appointment.is_deleted == False,
        )
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    t = appointment.appointment_time
    result = cancel_appointment.invoke({
        "appointment_year": t.year,
        "appointment_month": t.month,
        "appointment_day": t.day,
        "appointment_hour": t.hour,
        "appointment_minute": t.minute,
        "user_email": current_user.email,
    })
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Cancellation failed"))
    return result


@router.get("/all", response_model=List[AppointmentOut])
def list_all_appointments(
    db: DBSession = Depends(get_db),
):
    """Admin: list all non-deleted appointments."""
    appointments = (
        db.query(Appointment)
        .filter(Appointment.is_deleted == False)
        .order_by(Appointment.appointment_time.asc())
        .all()
    )
    return appointments
