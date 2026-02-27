"""
Visitor check-in routes.
Uses lazy imports of agent tools to avoid native module crashes at startup.
"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import Optional, List
from sqlalchemy.orm import Session as DBSession

from database.models import Visitor, User
from api.schemas import VisitorOut
from api.auth import get_db

router = APIRouter(prefix="/api/visitors", tags=["Visitors"])


@router.post("", status_code=201)
async def check_in_visitor(
    name: str = Form(...),
    purpose: str = Form(...),
    company: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: DBSession = Depends(get_db),
):
    """Register a walk-in visitor with optional photo upload."""
    from agent.tools import register_visitor  # lazy import
    image_bytes = None
    if image:
        image_bytes = await image.read()

    result = register_visitor.invoke({
        "name": name,
        "purpose": purpose,
        "company": company,
        "image_data": image_bytes,
    })
    return {"success": True, "message": result}


@router.get("", response_model=List[VisitorOut])
def list_visitors(
    db: DBSession = Depends(get_db),
):
    """List all visitor check-ins, most recent first."""
    visitors = (
        db.query(Visitor)
        .order_by(Visitor.check_in_time.desc())
        .limit(200)
        .all()
    )
    return visitors
