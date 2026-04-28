"""
Migration script to transfer data from JSON files to SQLite database.
This script reads all existing JSON files and populates the database tables.
"""

import json
import os
import shutil
from datetime import datetime
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import init_db, get_session
from database.models import User, Doctor, Appointment, DiseaseSpecialty, Visitor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# JSON file paths
DATA_DIR = "data"
USER_DATA_FILE = os.path.join(DATA_DIR, "user_data.json")
DOCTORS_FILE = os.path.join(DATA_DIR, "doctors.json")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.json")
DISEASE_SPECIALTIES_FILE = os.path.join(DATA_DIR, "disease_specialties.json")
VISITORS_FILE = "visitors_log.json"  # In root directory

# Backup suffix
BACKUP_SUFFIX = ".backup"


def backup_json_files():
    """Create backup copies of all JSON files."""
    logger.info("Creating backup of JSON files...")
    
    files_to_backup = [
        USER_DATA_FILE,
        DOCTORS_FILE,
        APPOINTMENTS_FILE,
        DISEASE_SPECIALTIES_FILE
    ]
    
    # Add visitors file if it exists
    if os.path.exists(VISITORS_FILE):
        files_to_backup.append(VISITORS_FILE)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = file_path + BACKUP_SUFFIX
            shutil.copy2(file_path, backup_path)
            logger.info(f"  ✓ Backed up: {file_path} → {backup_path}")
        else:
            logger.warning(f"  ⚠ File not found: {file_path}")


def load_json_file(file_path):
    """Load data from a JSON file."""
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"  ✓ Loaded: {file_path}")
        return data
    except Exception as e:
        logger.error(f"  ✗ Error loading {file_path}: {e}")
        return None


def migrate_users(session):
    """Migrate users from JSON to database."""
    logger.info("\n📊 Migrating Users...")
    
    # FIX BUG-N16: Warn about legacy password hashes.
    # Old systems may have used MD5/SHA-256 instead of bcrypt.
    # Storing those hashes as-is will make bcrypt.checkpw() fail for all migrated users.
    # Admin must force a password reset after migration, or pre-hash with bcrypt here.
    logger.warning(
        "⚠️  PASSWORD HASH WARNING: Migrated users will inherit their original password hashes.\n"
        "   If the legacy system used MD5/SHA-256, those users CANNOT log in until their\n"
        "   passwords are reset.  It is strongly recommended to:\n"
        "   1. Set is_active=False for all migrated users, OR\n"
        "   2. Send them a forced password-reset email after migration.\n"
        "   See BUG-N16 in new_bug_report_implementation_plan.md for details."
    )
    
    data = load_json_file(USER_DATA_FILE)
    if not data:
        return 0
    
    count = 0
    for email, user_info in data.items():
        try:
            # Check if user already exists
            existing = session.query(User).filter_by(email=email).first()
            if existing:
                logger.info(f"  ⚠ User already exists: {email}")
                continue
            
            user = User(
                email=email,
                password_hash=user_info['password']
            )
            session.add(user)
            count += 1
            logger.info(f"  ✓ Added user: {email}")
        except Exception as e:
            logger.error(f"  ✗ Error adding user {email}: {e}")
    
    session.commit()
    logger.info(f"✓ Migrated {count} users")
    return count


def migrate_doctors(session):
    """Migrate doctors from JSON to database."""
    logger.info("\n📊 Migrating Doctors...")
    
    data = load_json_file(DOCTORS_FILE)
    if not data:
        return 0
    
    count = 0
    for doctor_info in data:
        try:
            # Check if doctor already exists (by name and specialty)
            existing = session.query(Doctor).filter_by(
                name=doctor_info['name'],
                specialty=doctor_info['specialty']
            ).first()
            
            if existing:
                logger.info(f"  ⚠ Doctor already exists: {doctor_info['name']} ({doctor_info['specialty']})")
                continue
            
            doctor = Doctor(
                name=doctor_info['name'],
                specialty=doctor_info['specialty']
            )
            session.add(doctor)
            count += 1
            logger.info(f"  ✓ Added doctor: {doctor_info['name']} - {doctor_info['specialty']}")
        except Exception as e:
            logger.error(f"  ✗ Error adding doctor: {e}")
    
    session.commit()
    logger.info(f"✓ Migrated {count} doctors")
    return count


def migrate_disease_specialties(session):
    """Migrate disease-specialty mappings from JSON to database."""
    logger.info("\n📊 Migrating Disease Specialties...")
    
    data = load_json_file(DISEASE_SPECIALTIES_FILE)
    if not data:
        return 0
    
    count = 0
    for disease, specialty in data.items():
        try:
            # Check if mapping already exists
            existing = session.query(DiseaseSpecialty).filter_by(disease=disease).first()
            if existing:
                logger.info(f"  ⚠ Mapping already exists: {disease} → {specialty}")
                continue
            
            mapping = DiseaseSpecialty(
                disease=disease,
                specialty=specialty
            )
            session.add(mapping)
            count += 1
            logger.info(f"  ✓ Added mapping: {disease} → {specialty}")
        except Exception as e:
            logger.error(f"  ✗ Error adding mapping for {disease}: {e}")
    
    session.commit()
    logger.info(f"✓ Migrated {count} disease-specialty mappings")
    return count


def migrate_appointments(session):
    """Migrate appointments from JSON to database."""
    logger.info("\n📊 Migrating Appointments...")
    
    data = load_json_file(APPOINTMENTS_FILE)
    if not data:
        return 0
    
    count = 0
    for appt_info in data:
        try:
            # Parse the datetime string
            appt_time = datetime.fromisoformat(appt_info['time'])
            
            # Check if appointment already exists
            existing = session.query(Appointment).filter_by(
                user_email=appt_info['user'],
                doctor_name=appt_info['doctor'],
                appointment_time=appt_time
            ).first()
            
            if existing:
                logger.info(f"  ⚠ Appointment already exists: {appt_info['user']} with {appt_info['doctor']} at {appt_time}")
                continue
            
            appointment = Appointment(
                user_email=appt_info['user'],
                doctor_name=appt_info['doctor'],
                disease=appt_info['disease'],
                appointment_time=appt_time
            )
            session.add(appointment)
            count += 1
            logger.info(f"  ✓ Added appointment: {appt_info['user']} with {appt_info['doctor']} at {appt_time}")
        except Exception as e:
            logger.error(f"  ✗ Error adding appointment: {e}")
    
    session.commit()
    logger.info(f"✓ Migrated {count} appointments")
    return count


def migrate_visitors(session):
    """Migrate visitors from JSON to database."""
    logger.info("\n📊 Migrating Visitors...")
    
    data = load_json_file(VISITORS_FILE)
    if not data:
        logger.info("  ℹ No visitors file found or no data")
        return 0
    
    count = 0
    for visitor_info in data:
        try:
            # Parse the datetime string
            check_in_time = datetime.fromisoformat(visitor_info.get('timestamp', visitor_info.get('check_in_time', datetime.now().isoformat())))
            
            visitor = Visitor(
                name=visitor_info['name'],
                purpose=visitor_info['purpose'],
                company=visitor_info.get('company', ''),
                check_in_time=check_in_time,
                image_path=visitor_info.get('image_path', None)
            )
            session.add(visitor)
            count += 1
            logger.info(f"  ✓ Added visitor: {visitor_info['name']} - {visitor_info['purpose']}")
        except Exception as e:
            logger.error(f"  ✗ Error adding visitor: {e}")
    
    session.commit()
    logger.info(f"✓ Migrated {count} visitors")
    return count


def print_migration_report(stats):
    """Print a summary report of the migration."""
    print("\n" + "="*60)
    print("📋 MIGRATION REPORT")
    print("="*60)
    print(f"Users migrated:              {stats['users']}")
    print(f"Doctors migrated:            {stats['doctors']}")
    print(f"Disease specialties:         {stats['disease_specialties']}")
    print(f"Appointments migrated:       {stats['appointments']}")
    print(f"Visitors migrated:           {stats['visitors']}")
    print("="*60)
    print(f"Total records migrated:      {sum(stats.values())}")
    print("="*60)


def main():
    """Main migration function."""
    print("\n" + "="*60)
    print("🚀 AI RECEPTIONIST - JSON TO DATABASE MIGRATION")
    print("="*60)
    
    # Step 1: Backup JSON files
    backup_json_files()
    
    # Step 2: Initialize database
    logger.info("\n🔧 Initializing database...")
    if not init_db():
        logger.error("✗ Failed to initialize database. Aborting migration.")
        return
    logger.info("✓ Database initialized successfully")
    
    # Step 3: Migrate data
    session = get_session()
    stats = {}
    
    try:
        # Migrate in order (respecting dependencies)
        stats['users'] = migrate_users(session)
        stats['doctors'] = migrate_doctors(session)
        stats['disease_specialties'] = migrate_disease_specialties(session)
        stats['appointments'] = migrate_appointments(session)
        stats['visitors'] = migrate_visitors(session)
        
        # Step 4: Print report
        print_migration_report(stats)
        
        logger.info("\n✅ Migration completed successfully!")
        logger.info(f"✅ Database file created: receptionist.db")
        logger.info(f"✅ JSON backups created with '{BACKUP_SUFFIX}' suffix")
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
