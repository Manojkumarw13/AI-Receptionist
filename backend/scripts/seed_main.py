"""
Seed the main operational database (receptionist.db) with doctors, disease→specialty
mappings, and a default admin user so the AI agent works out of the box.

Run standalone:  python -m scripts.seed_main
Or: called automatically by main.py on first startup.
"""

import os
import sys
import logging

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session, init_db
from database.models import Doctor, DiseaseSpecialty, User
from api.auth import hash_password

logger = logging.getLogger(__name__)


# ── Doctors ──────────────────────────────────────────────────────────────────
DOCTORS = [
    # Cardiology
    ("Dr. Sarah Johnson", "Cardiology"),
    ("Dr. Rajesh Kumar", "Cardiology"),
    ("Dr. Emily Chen", "Cardiology"),
    # Neurology
    ("Dr. Michael Brown", "Neurology"),
    ("Dr. Priya Sharma", "Neurology"),
    # Pediatrics
    ("Dr. Jennifer Wilson", "Pediatrics"),
    ("Dr. Suresh Reddy", "Pediatrics"),
    ("Dr. Lisa Anderson", "Pediatrics"),
    # Orthopedics
    ("Dr. James Taylor", "Orthopedics"),
    ("Dr. Ramesh Gupta", "Orthopedics"),
    # Dermatology
    ("Dr. Emily Davis", "Dermatology"),
    ("Dr. Vikram Malhotra", "Dermatology"),
    # Gynecology
    ("Dr. Maria Rodriguez", "Gynecology"),
    ("Dr. Lakshmi Menon", "Gynecology"),
    # ENT
    ("Dr. William Thomas", "ENT"),
    ("Dr. Arun Verma", "ENT"),
    # Ophthalmology
    ("Dr. Christopher White", "Ophthalmology"),
    ("Dr. Sunita Rao", "Ophthalmology"),
    # General Medicine
    ("Dr. Richard Clark", "General Medicine"),
    ("Dr. Vijay Kumar", "General Medicine"),
    ("Dr. Susan Lewis", "General Medicine"),
    # Psychiatry
    ("Dr. Elizabeth Martin", "Psychiatry"),
    ("Dr. Kiran Bedi", "Psychiatry"),
    # Gastroenterology
    ("Dr. Joseph Walker", "Gastroenterology"),
    # Pulmonology
    ("Dr. Charles Allen", "Pulmonology"),
    # Endocrinology
    ("Dr. Thomas King", "Endocrinology"),
    # Urology
    ("Dr. Steven Scott", "Urology"),
    # Oncology
    ("Dr. Paul Adams", "Oncology"),
]

# ── Disease → Specialty mapping ──────────────────────────────────────────────
DISEASE_SPECIALTIES = [
    ("Hypertension", "Cardiology"),
    ("Coronary Artery Disease", "Cardiology"),
    ("Arrhythmia", "Cardiology"),
    ("Heart Failure", "Cardiology"),
    ("Migraine", "Neurology"),
    ("Epilepsy", "Neurology"),
    ("Stroke", "Neurology"),
    ("Chickenpox", "Pediatrics"),
    ("Measles", "Pediatrics"),
    ("Asthma", "Pediatrics"),
    ("Arthritis", "Orthopedics"),
    ("Fracture", "Orthopedics"),
    ("Osteoporosis", "Orthopedics"),
    ("Eczema", "Dermatology"),
    ("Psoriasis", "Dermatology"),
    ("Acne", "Dermatology"),
    ("PCOS", "Gynecology"),
    ("Endometriosis", "Gynecology"),
    ("Sinusitis", "ENT"),
    ("Hearing Loss", "ENT"),
    ("Vertigo", "ENT"),
    ("Cataract", "Ophthalmology"),
    ("Glaucoma", "Ophthalmology"),
    ("Depression", "Psychiatry"),
    ("Anxiety", "Psychiatry"),
    ("Diabetes", "General Medicine"),
    ("Thyroid Disorder", "General Medicine"),
    ("Anemia", "General Medicine"),
    ("Fever", "General Medicine"),
    ("GERD", "Gastroenterology"),
    ("IBS", "Gastroenterology"),
    ("Bronchitis", "Pulmonology"),
    ("Pneumonia", "Pulmonology"),
    ("COPD", "Pulmonology"),
    ("Kidney Stones", "Urology"),
    ("Breast Cancer", "Oncology"),
    ("Lung Cancer", "Oncology"),
    ("Diabetes Type 1", "Endocrinology"),
    ("Hyperthyroidism", "Endocrinology"),
]

# BUG-03 FIX: Read seed passwords from environment variables.
# NEVER use trivially guessable defaults (admin123/user123) in production.
# Set SEED_ADMIN_PASSWORD and SEED_USER_PASSWORD in your .env file.
_DEFAULT_ADMIN_PW = os.getenv("SEED_ADMIN_PASSWORD", "")
_DEFAULT_USER_PW = os.getenv("SEED_USER_PASSWORD", "")

if not _DEFAULT_ADMIN_PW:
    logger.warning(
        "⚠️  SEED_ADMIN_PASSWORD not set in .env. "
        "Default demo account will NOT be created. Set it to seed an admin user."
    )
if not _DEFAULT_USER_PW:
    logger.warning(
        "⚠️  SEED_USER_PASSWORD not set in .env. "
        "Default demo account will NOT be created. Set it to seed a standard user."
    )


def seed_if_empty():
    """Populate the main DB with doctors and disease mappings if it is empty."""
    session = get_session()
    try:
        existing_doctors = session.query(Doctor).count()
        if existing_doctors > 0:
            logger.info(f"Main DB already seeded ({existing_doctors} doctors). Skipping.")
            return

        logger.info("Main DB is empty — seeding doctors and disease specialties...")

        # Doctors
        for name, specialty in DOCTORS:
            session.add(Doctor(name=name, specialty=specialty))

        # Disease → Specialty
        for disease, specialty in DISEASE_SPECIALTIES:
            session.add(DiseaseSpecialty(disease=disease, specialty=specialty))

        # Default Users — only if passwords are configured
        if session.query(User).count() == 0:
            if _DEFAULT_ADMIN_PW:
                admin_user = User(
                    email="admin@example.com",
                    password_hash=hash_password(_DEFAULT_ADMIN_PW),
                    name="Admin User",
                    role="admin",
                    is_active=True
                )
                session.add(admin_user)
                logger.info("Admin seed user created (admin@example.com).")

            if _DEFAULT_USER_PW:
                standard_user = User(
                    email="user@example.com",
                    password_hash=hash_password(_DEFAULT_USER_PW),
                    name="Test Patient",
                    role="user",
                    is_active=True
                )
                session.add(standard_user)
                logger.info("Standard seed user created (user@example.com).")

        session.commit()
        logger.info(
            f"Seeded {len(DOCTORS)} doctors, {len(DISEASE_SPECIALTIES)} disease-specialty mappings."
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding main DB: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    seed_if_empty()
    print("Done.")
