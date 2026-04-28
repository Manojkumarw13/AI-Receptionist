import sys
import os

# Ensure backend acts as the root module for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
    
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Old operational models
from database.models import User as OldUser, Doctor as OldDoctor, Appointment as OldAppointment, DiseaseSpecialty as OldDiseaseSpecialty, Visitor as OldVisitor
# New star models
from database.models_star import (
    Base as StarBase, DimUser, DimDoctor, DimDisease, 
    DimVisitor, FactAppointment, FactVisitorCheckIn
)
from database.connection import get_or_create_date_dimension, get_or_create_time_dimension

# Setup connections
old_db_path = os.path.join(BASE_DIR, "receptionist.db")
new_db_path = os.path.join(BASE_DIR, "receptionist_star.db")

old_engine = create_engine(f"sqlite:///{old_db_path}")
new_engine = create_engine(f"sqlite:///{new_db_path}")

OldSession = sessionmaker(bind=old_engine)
NewSession = sessionmaker(bind=new_engine)

def migrate_users(old_session, new_session):
    print("Migrating users...")
    old_users = old_session.query(OldUser).all()
    for u in old_users:
        if not new_session.query(DimUser).filter_by(email=u.email).first():
            new_u = DimUser(
                email=u.email,
                password_hash=u.password_hash,
                role=u.role,
                full_name=u.name or "Unknown User",
                created_at=u.created_at,
                last_login=u.last_login,
                is_active=u.is_active
            )
            new_session.add(new_u)
    new_session.commit()
    print(f"Migrated {len(old_users)} users.")

def migrate_doctors(old_session, new_session):
    print("Migrating doctors...")
    old_docs = old_session.query(OldDoctor).all()
    for d in old_docs:
        if not new_session.query(DimDoctor).filter_by(name=d.name).first():
            # mock some fields that might not be in the operational table but are required in dim
            new_doc = DimDoctor(
                name=d.name,
                specialty=d.specialty,
                qualification="Migrated",
                experience_years=5,
                rating=4.5,
                consultation_fee=500.0,
                is_active=True
            )
            new_session.add(new_doc)
    new_session.commit()
    print(f"Migrated {len(old_docs)} doctors.")

def migrate_diseases(old_session, new_session):
    print("Migrating diseases...")
    old_ds = old_session.query(OldDiseaseSpecialty).all()
    for ds in old_ds:
        if not new_session.query(DimDisease).filter_by(disease_name=ds.disease).first():
            new_disease = DimDisease(
                disease_name=ds.disease,
                specialty=ds.specialty,
                category="General",
                severity="Moderate"
            )
            new_session.add(new_disease)
    new_session.commit()
    print(f"Migrated {len(old_ds)} diseases.")

def migrate_visitors_and_checkins(old_session, new_session):
    print("Migrating visitors...")
    old_visitors = old_session.query(OldVisitor).all()
    for v in old_visitors:
        # Create DimVisitor
        dim_v = new_session.query(DimVisitor).filter_by(name=v.name, company=v.company).first()
        if not dim_v:
            dim_v = DimVisitor(
                name=v.name,
                company=v.company,
                purpose=v.purpose
            )
            new_session.add(dim_v)
            new_session.flush() # get ID

        # Create checkin fact
        d_dim = get_or_create_date_dimension(new_session, v.check_in_time.date())
        t_dim = get_or_create_time_dimension(new_session, v.check_in_time.time())
        
        # Check if we already migrated it
        fact = new_session.query(FactVisitorCheckIn).filter_by(
            visitor_id=dim_v.visitor_id, 
            date_id=d_dim.date_id, 
            time_id=t_dim.time_id
        ).first()

        if not fact:
            new_fact = FactVisitorCheckIn(
                date_id=d_dim.date_id,
                time_id=t_dim.time_id,
                visitor_id=dim_v.visitor_id,
                checkin_time=v.check_in_time,
                image_path=v.image_path,
                notes=v.purpose
            )
            new_session.add(new_fact)

    new_session.commit()
    print(f"Migrated {len(old_visitors)} visitors and checkins.")

def migrate_appointments(old_session, new_session):
    print("Migrating appointments...")
    old_apps = old_session.query(OldAppointment).all()
    for app in old_apps:
        user = new_session.query(DimUser).filter_by(email=app.user_email).first()
        doc = new_session.query(DimDoctor).filter_by(name=app.doctor_name).first()
        disease = new_session.query(DimDisease).filter_by(disease_name=app.disease).first()

        if not user or not doc or not disease:
            print(f"Skipping appointment {app.id}: missing foreign keys in star DB.", end=" ")
            if not user: print("No User;", end="")
            if not doc: print("No Doc;", end="")
            if not disease: print("No Disease;", end="")
            print()
            continue
            
        d_dim = get_or_create_date_dimension(new_session, app.appointment_time.date())
        t_dim = get_or_create_time_dimension(new_session, app.appointment_time.time())

        # Check existing
        fact = new_session.query(FactAppointment).filter_by(
            user_id=user.user_id,
            doctor_id=doc.doctor_id,
            date_id=d_dim.date_id,
            time_id=t_dim.time_id
        ).first()

        if not fact:
            new_fact = FactAppointment(
                date_id=d_dim.date_id,
                time_id=t_dim.time_id,
                doctor_id=doc.doctor_id,
                user_id=user.user_id,
                disease_id=disease.disease_id,
                status=app.status,
                created_at=app.created_at,
                updated_at=app.updated_at
            )
            new_session.add(new_fact)
    
    new_session.commit()
    print(f"Migrated up to {len(old_apps)} appointments.")


def migrate_all():
    print("Connecting databases...")
    old_session = OldSession()
    new_session = NewSession()

    try:
        # Ensures all tables are created on the star schema side
        StarBase.metadata.create_all(bind=new_engine)
        
        migrate_users(old_session, new_session)
        migrate_doctors(old_session, new_session)
        migrate_diseases(old_session, new_session)
        migrate_visitors_and_checkins(old_session, new_session)
        migrate_appointments(old_session, new_session)
        
        print("Migration complete.")
    finally:
        old_session.close()
        new_session.close()

if __name__ == "__main__":
    migrate_all()
