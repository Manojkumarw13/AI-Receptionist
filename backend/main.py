"""
AI Receptionist – FastAPI entry point.

Run with:
    cd backend
    uvicorn main:app --reload --port 8000
"""
import sys
import os

# Ensure the backend directory is on the path so absolute imports work
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from database.connection import init_db, init_star_db
from api.routes.auth_routes import router as auth_router
from api.routes.appointment_routes import router as appointment_router
from api.routes.doctor_routes import router as doctor_router
from api.routes.visitor_routes import router as visitor_router
from api.routes.availability_routes import router as availability_router
from api.routes.chat_routes import router as chat_router
from config import IMAGES_DIR

# ── Application setup ─────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Receptionist API",
    description=(
        "REST API for the AI Receptionist system. "
        "Provides endpoints for authentication, appointment booking/cancellation, "
        "doctor listing, visitor check-in, and an AI chat interface backed by "
        "a LangGraph agent."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (visitor images / QR codes) ──────────────────────────────────

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(appointment_router)
app.include_router(doctor_router)
app.include_router(visitor_router)
app.include_router(availability_router)
app.include_router(chat_router)

# ── Startup / Shutdown events ─────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    """Initialize databases on startup."""
    init_db()
    init_star_db()


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    """Quick liveness probe."""
    return {"status": "healthy", "service": "AI Receptionist API", "version": "1.0.0"}


@app.get("/health/ready", tags=["Health"])
def readiness():
    """Readiness probe – verifies DB connection."""
    from database.connection import check_db_exists
    db_ok = check_db_exists()
    return {
        "ready": db_ok,
        "database": "ok" if db_ok else "unavailable",
    }


@app.get("/", tags=["Root"])
def root():
    """API root – redirect hint."""
    return {
        "message": "AI Receptionist API is running.",
        "docs": "/docs",
        "health": "/health",
    }
