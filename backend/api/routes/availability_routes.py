"""
Availability routes: find next open slot.
Uses lazy imports of agent tools to avoid native module crashes at startup.
"""
from fastapi import APIRouter, Depends

from api.schemas import AvailabilityResponse
from api.auth import get_current_user
from database.models import User

router = APIRouter(prefix="/api/availability", tags=["Availability"])


@router.get("", response_model=AvailabilityResponse)
def get_availability(
    current_user: User = Depends(get_current_user),
):
    """Return the next available appointment slot."""
    from agent.tools import get_next_available_appointment  # lazy import
    result = get_next_available_appointment.invoke({})
    return result
