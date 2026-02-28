"""
Visitor check-in routes.
Uses lazy imports of agent tools to avoid native module crashes at startup.
"""
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from typing import Optional, List
from sqlalchemy.orm import Session as DBSession

from database.models import Visitor, User
from api.schemas import VisitorOut
from api.auth import get_db

router = APIRouter(prefix="/api/visitors", tags=["Visitors"])

# Fix #2: Upload security constants
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


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
        # Fix #2: Validate MIME type
        if image.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type '{image.content_type}'. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
            )
        # Fix #2: Read with size limit to prevent OOM
        image_bytes = await image.read(MAX_IMAGE_SIZE + 1)
        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB."
            )

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

