"""
Doctor routes: list all doctors and filter by specialty.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional

from database.models import Doctor
from api.schemas import DoctorOut
from api.auth import get_db

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


@router.get("", response_model=List[DoctorOut])
def list_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    db: DBSession = Depends(get_db),
):
    """Return all doctors, optionally filtering by specialty."""
    query = db.query(Doctor)
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
    return query.order_by(Doctor.specialty, Doctor.name).all()


@router.get("/specialties")
def list_specialties(db: DBSession = Depends(get_db)):
    """Return a distinct list of all specialties available."""
    rows = db.query(Doctor.specialty).distinct().order_by(Doctor.specialty).all()
    return [r.specialty for r in rows]
