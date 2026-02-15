"""
Populate Star Schema Database with Comprehensive Sample Data
Generates realistic data for all dimension and fact tables
"""

import sys
import logging
from datetime import datetime, date, time, timedelta
import random
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import star schema models
from models_star import (
    Base, DimDate, DimTime, DimDoctor, DimUser, DimDisease,
    DimVisitor, FactAppointment, FactVisitorCheckIn
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "sqlite:///receptionist_star.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


# ==================== DATA GENERATORS ====================

def generate_date_dimension(start_year=2024, end_year=2026):
    """Generate date dimension for 3 years."""
    logger.info("Generating date dimension...")
    dates = []
    
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    current_date = start_date
    
    # Indian holidays (simplified)
    holidays = {
        (1, 26): "Republic Day",
        (8, 15): "Independence Day",
        (10, 2): "Gandhi Jayanti",
        (12, 25): "Christmas"
    }
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        is_weekend = day_of_week >= 5
        
        holiday_name = holidays.get((current_date.month, current_date.day))
        is_holiday = holiday_name is not None
        
        dim_date = DimDate(
            full_date=current_date,
            year=current_date.year,
            quarter=(current_date.month - 1) // 3 + 1,
            month=current_date.month,
            month_name=month_names[current_date.month - 1],
            day=current_date.day,
            day_of_week=day_of_week,
            day_name=day_names[day_of_week],
            week_of_year=current_date.isocalendar()[1],
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            holiday_name=holiday_name
        )
        dates.append(dim_date)
        current_date += timedelta(days=1)
    
    logger.info(f"Generated {len(dates)} date records")
    return dates


def generate_time_dimension():
    """Generate time dimension with 30-minute slots from 08:00 to 20:00."""
    logger.info("Generating time dimension...")
    times = []
    
    start_hour = 8
    end_hour = 20
    
    for hour in range(start_hour, end_hour + 1):
        for minute in [0, 30]:
            if hour == end_hour and minute == 30:
                break
            
            time_value = time(hour, minute)
            next_minute = 30 if minute == 0 else 0
            next_hour = hour if minute == 0 else hour + 1
            
            time_slot = f"{hour:02d}:{minute:02d}-{next_hour:02d}:{next_minute:02d}"
            
            # Determine period
            if hour < 12:
                period = "Morning"
            elif hour < 17:
                period = "Afternoon"
            elif hour < 20:
                period = "Evening"
            else:
                period = "Night"
            
            # Business hours: 9 AM to 6 PM
            is_business_hours = 9 <= hour < 18
            
            dim_time = DimTime(
                time_value=time_value,
                hour=hour,
                minute=minute,
                time_slot=time_slot,
                period=period,
                is_business_hours=is_business_hours
            )
            times.append(dim_time)
    
    logger.info(f"Generated {len(times)} time slots")
    return times


def generate_doctor_dimension():
    """Generate 50+ doctors across 15 specialties."""
    logger.info("Generating doctor dimension...")
    
    specialties = {
        "Cardiology": ["Dr. Sarah Johnson", "Dr. Rajesh Kumar", "Dr. Emily Chen", "Dr. Amit Patel"],
        "Neurology": ["Dr. Michael Brown", "Dr. Priya Sharma", "Dr. David Lee", "Dr. Anita Desai"],
        "Pediatrics": ["Dr. Jennifer Wilson", "Dr. Suresh Reddy", "Dr. Lisa Anderson", "Dr. Kavita Singh"],
        "Orthopedics": ["Dr. James Taylor", "Dr. Ramesh Gupta", "Dr. Robert Martinez", "Dr. Deepa Nair"],
        "Dermatology": ["Dr. Emily Davis", "Dr. Vikram Malhotra", "Dr. Jessica Garcia", "Dr. Sneha Iyer"],
        "Gynecology": ["Dr. Maria Rodriguez", "Dr. Lakshmi Menon", "Dr. Patricia Moore", "Dr. Ritu Kapoor"],
        "ENT": ["Dr. William Thomas", "Dr. Arun Verma", "Dr. Nancy Jackson", "Dr. Pooja Joshi"],
        "Ophthalmology": ["Dr. Christopher White", "Dr. Sunita Rao", "Dr. Daniel Harris", "Dr. Meera Pillai"],
        "Psychiatry": ["Dr. Elizabeth Martin", "Dr. Kiran Bedi", "Dr. Matthew Thompson", "Dr. Anjali Mehta"],
        "General Medicine": ["Dr. Richard Clark", "Dr. Vijay Kumar", "Dr. Susan Lewis", "Dr. Nisha Agarwal"],
        "Gastroenterology": ["Dr. Joseph Walker", "Dr. Sanjay Chopra", "Dr. Karen Hall", "Dr. Divya Krishnan"],
        "Pulmonology": ["Dr. Charles Allen", "Dr. Ashok Sharma", "Dr. Linda Young", "Dr. Radha Iyer"],
        "Endocrinology": ["Dr. Thomas King", "Dr. Madhavi Reddy", "Dr. Barbara Wright", "Dr. Shalini Gupta"],
        "Urology": ["Dr. Steven Scott", "Dr. Prakash Jain", "Dr. Michelle Green", "Dr. Swati Deshmukh"],
        "Oncology": ["Dr. Paul Adams", "Dr. Ramya Krishnan", "Dr. Sandra Baker", "Dr. Neha Bansal"]
    }
    
    qualifications = ["MBBS, MD", "MBBS, MS", "MBBS, DNB", "MBBS, DM", "MBBS, MCh"]
    
    doctors = []
    for specialty, names in specialties.items():
        for name in names:
            doctor = DimDoctor(
                name=name,
                specialty=specialty,
                qualification=random.choice(qualifications),
                experience_years=random.randint(5, 25),
                rating=round(random.uniform(4.0, 5.0), 1),
                consultation_fee=random.choice([500, 600, 750, 800, 1000, 1200, 1500]),
                phone=f"+91-{random.randint(7000000000, 9999999999)}",
                email=f"{name.lower().replace(' ', '.').replace('dr.', '')}@aurahospital.com",
                availability="Mon-Sat 9AM-6PM",
                is_active=True
            )
            doctors.append(doctor)
    
    logger.info(f"Generated {len(doctors)} doctors across {len(specialties)} specialties")
    return doctors


def generate_user_dimension():
    """Generate 100+ sample patients."""
    logger.info("Generating user dimension...")
    
    first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rohan", "Kavita",
                   "Arjun", "Divya", "Karan", "Pooja", "Aditya", "Neha", "Sanjay", "Ritu",
                   "Rajesh", "Meera", "Suresh", "Lakshmi", "Vijay", "Swati", "Ashok", "Radha"]
    
    last_names = ["Sharma", "Kumar", "Patel", "Singh", "Reddy", "Gupta", "Iyer", "Nair",
                  "Desai", "Mehta", "Joshi", "Verma", "Agarwal", "Chopra", "Malhotra", "Kapoor"]
    
    cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"]
    states = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana", "Maharashtra", "West Bengal", "Gujarat"]
    
    blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
    genders = ["Male", "Female", "Other"]
    
    users = []
    for i in range(100):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
        
        city_idx = random.randint(0, len(cities) - 1)
        
        user = DimUser(
            email=email,
            password_hash=hashlib.sha256("password123".encode()).hexdigest(),
            full_name=full_name,
            phone=f"+91-{random.randint(7000000000, 9999999999)}",
            age=random.randint(18, 75),
            gender=random.choice(genders),
            blood_group=random.choice(blood_groups),
            address=f"{random.randint(1, 999)} MG Road",
            city=cities[city_idx],
            state=states[city_idx],
            pincode=f"{random.randint(100000, 999999)}",
            emergency_contact=f"+91-{random.randint(7000000000, 9999999999)}",
            is_active=True
        )
        users.append(user)
    
    logger.info(f"Generated {len(users)} users")
    return users


def generate_disease_dimension():
    """Generate 100+ diseases with specialty mappings."""
    logger.info("Generating disease dimension...")
    
    diseases_data = [
        # Cardiology
        ("Hypertension", "Cardiology", "Chronic", "Moderate", "High blood pressure", "Headache, dizziness", "I10"),
        ("Coronary Artery Disease", "Cardiology", "Chronic", "Severe", "Heart disease", "Chest pain, shortness of breath", "I25"),
        ("Arrhythmia", "Cardiology", "Chronic", "Moderate", "Irregular heartbeat", "Palpitations, dizziness", "I49"),
        ("Heart Failure", "Cardiology", "Chronic", "Severe", "Weak heart pump", "Fatigue, swelling", "I50"),
        
        # Neurology
        ("Migraine", "Neurology", "Episodic", "Moderate", "Severe headache", "Throbbing pain, nausea", "G43"),
        ("Epilepsy", "Neurology", "Chronic", "Severe", "Seizure disorder", "Seizures, loss of consciousness", "G40"),
        ("Parkinson's Disease", "Neurology", "Chronic", "Severe", "Movement disorder", "Tremors, stiffness", "G20"),
        ("Stroke", "Neurology", "Acute", "Severe", "Brain attack", "Weakness, speech difficulty", "I64"),
        
        # Pediatrics
        ("Chickenpox", "Pediatrics", "Infectious", "Mild", "Viral infection", "Rash, fever", "B01"),
        ("Measles", "Pediatrics", "Infectious", "Moderate", "Viral infection", "Rash, cough, fever", "B05"),
        ("Asthma", "Pediatrics", "Chronic", "Moderate", "Breathing difficulty", "Wheezing, cough", "J45"),
        ("Tonsillitis", "Pediatrics", "Acute", "Mild", "Throat infection", "Sore throat, fever", "J03"),
        
        # Orthopedics
        ("Arthritis", "Orthopedics", "Chronic", "Moderate", "Joint inflammation", "Pain, stiffness", "M19"),
        ("Fracture", "Orthopedics", "Acute", "Moderate", "Broken bone", "Pain, swelling", "S82"),
        ("Osteoporosis", "Orthopedics", "Chronic", "Moderate", "Weak bones", "Bone pain, fractures", "M81"),
        ("Sprain", "Orthopedics", "Acute", "Mild", "Ligament injury", "Pain, swelling", "S93"),
        
        # Dermatology
        ("Eczema", "Dermatology", "Chronic", "Mild", "Skin inflammation", "Itching, redness", "L30"),
        ("Psoriasis", "Dermatology", "Chronic", "Moderate", "Skin condition", "Scaly patches", "L40"),
        ("Acne", "Dermatology", "Chronic", "Mild", "Skin condition", "Pimples, blackheads", "L70"),
        ("Fungal Infection", "Dermatology", "Infectious", "Mild", "Skin infection", "Itching, rash", "B35"),
        
        # Gynecology
        ("PCOS", "Gynecology", "Chronic", "Moderate", "Hormonal disorder", "Irregular periods, weight gain", "E28"),
        ("Endometriosis", "Gynecology", "Chronic", "Moderate", "Tissue growth", "Pelvic pain", "N80"),
        ("Menstrual Disorders", "Gynecology", "Episodic", "Mild", "Period problems", "Irregular bleeding", "N92"),
        ("UTI", "Gynecology", "Acute", "Mild", "Urinary infection", "Burning, frequency", "N39"),
        
        # ENT
        ("Sinusitis", "ENT", "Acute", "Mild", "Sinus infection", "Facial pain, congestion", "J32"),
        ("Tinnitus", "ENT", "Chronic", "Mild", "Ear ringing", "Ringing sound", "H93"),
        ("Hearing Loss", "ENT", "Chronic", "Moderate", "Reduced hearing", "Difficulty hearing", "H91"),
        ("Vertigo", "ENT", "Episodic", "Moderate", "Dizziness", "Spinning sensation", "H81"),
        
        # Ophthalmology
        ("Cataract", "Ophthalmology", "Chronic", "Moderate", "Lens clouding", "Blurred vision", "H25"),
        ("Glaucoma", "Ophthalmology", "Chronic", "Severe", "Eye pressure", "Vision loss", "H40"),
        ("Conjunctivitis", "Ophthalmology", "Acute", "Mild", "Eye infection", "Redness, discharge", "H10"),
        ("Myopia", "Ophthalmology", "Chronic", "Mild", "Nearsightedness", "Blurred distance vision", "H52"),
        
        # Psychiatry
        ("Depression", "Psychiatry", "Chronic", "Moderate", "Mood disorder", "Sadness, loss of interest", "F32"),
        ("Anxiety", "Psychiatry", "Chronic", "Moderate", "Excessive worry", "Restlessness, tension", "F41"),
        ("OCD", "Psychiatry", "Chronic", "Moderate", "Obsessive thoughts", "Repetitive behaviors", "F42"),
        ("PTSD", "Psychiatry", "Chronic", "Severe", "Trauma disorder", "Flashbacks, nightmares", "F43"),
        
        # General Medicine
        ("Diabetes Type 2", "General Medicine", "Chronic", "Moderate", "High blood sugar", "Thirst, fatigue", "E11"),
        ("Thyroid Disorder", "General Medicine", "Chronic", "Moderate", "Thyroid dysfunction", "Weight changes, fatigue", "E03"),
        ("Anemia", "General Medicine", "Chronic", "Mild", "Low hemoglobin", "Fatigue, weakness", "D50"),
        ("Fever", "General Medicine", "Acute", "Mild", "High temperature", "Body ache, chills", "R50"),
        
        # Gastroenterology
        ("GERD", "Gastroenterology", "Chronic", "Moderate", "Acid reflux", "Heartburn, regurgitation", "K21"),
        ("IBS", "Gastroenterology", "Chronic", "Moderate", "Bowel disorder", "Abdominal pain, bloating", "K58"),
        ("Hepatitis", "Gastroenterology", "Infectious", "Severe", "Liver inflammation", "Jaundice, fatigue", "B19"),
        ("Gastritis", "Gastroenterology", "Acute", "Mild", "Stomach inflammation", "Nausea, pain", "K29"),
        
        # Pulmonology
        ("Bronchitis", "Pulmonology", "Acute", "Mild", "Airway inflammation", "Cough, mucus", "J20"),
        ("Pneumonia", "Pulmonology", "Acute", "Severe", "Lung infection", "Fever, cough, chest pain", "J18"),
        ("COPD", "Pulmonology", "Chronic", "Severe", "Lung disease", "Breathing difficulty", "J44"),
        ("Tuberculosis", "Pulmonology", "Infectious", "Severe", "Bacterial infection", "Cough, weight loss", "A15"),
        
        # Endocrinology
        ("Diabetes Type 1", "Endocrinology", "Chronic", "Severe", "Insulin deficiency", "Thirst, urination", "E10"),
        ("Hyperthyroidism", "Endocrinology", "Chronic", "Moderate", "Overactive thyroid", "Weight loss, anxiety", "E05"),
        ("Hypothyroidism", "Endocrinology", "Chronic", "Moderate", "Underactive thyroid", "Weight gain, fatigue", "E03"),
        ("Cushing Syndrome", "Endocrinology", "Chronic", "Severe", "Excess cortisol", "Weight gain, weakness", "E24"),
        
        # Urology
        ("Kidney Stones", "Urology", "Acute", "Severe", "Mineral deposits", "Severe pain, blood in urine", "N20"),
        ("Prostate Enlargement", "Urology", "Chronic", "Moderate", "BPH", "Urinary frequency", "N40"),
        ("Bladder Infection", "Urology", "Acute", "Mild", "Cystitis", "Burning, urgency", "N30"),
        ("Kidney Infection", "Urology", "Acute", "Severe", "Pyelonephritis", "Fever, back pain", "N10"),
        
        # Oncology
        ("Breast Cancer", "Oncology", "Chronic", "Severe", "Malignant tumor", "Lump, discharge", "C50"),
        ("Lung Cancer", "Oncology", "Chronic", "Severe", "Malignant tumor", "Cough, weight loss", "C34"),
        ("Leukemia", "Oncology", "Chronic", "Severe", "Blood cancer", "Fatigue, infections", "C91"),
        ("Lymphoma", "Oncology", "Chronic", "Severe", "Lymph node cancer", "Swollen nodes, fever", "C85"),
    ]
    
    diseases = []
    for disease_data in diseases_data:
        disease = DimDisease(
            disease_name=disease_data[0],
            specialty=disease_data[1],
            category=disease_data[2],
            severity=disease_data[3],
            description=disease_data[4],
            common_symptoms=disease_data[5],
            icd_code=disease_data[6]
        )
        diseases.append(disease)
    
    logger.info(f"Generated {len(diseases)} diseases")
    return diseases


def generate_visitor_dimension():
    """Generate sample visitors."""
    logger.info("Generating visitor dimension...")
    
    visitor_names = ["Amit Verma", "Priya Kapoor", "Rajesh Gupta", "Sneha Reddy", "Vikram Malhotra",
                     "Anjali Sharma", "Rohan Patel", "Divya Iyer", "Karan Singh", "Pooja Nair"]
    
    companies = ["TCS", "Infosys", "Wipro", "Accenture", "IBM", "Google", "Microsoft", "Amazon", "Self-Employed", None]
    purposes = ["Meeting", "Delivery", "Interview", "Consultation", "Vendor Visit", "Personal Visit"]
    id_types = ["Aadhar", "PAN", "Driving License", "Passport"]
    
    visitors = []
    for i, name in enumerate(visitor_names):
        visitor = DimVisitor(
            name=name,
            company=random.choice(companies),
            purpose=random.choice(purposes),
            contact=f"+91-{random.randint(7000000000, 9999999999)}",
            email=f"{name.lower().replace(' ', '.')}@example.com",
            id_type=random.choice(id_types),
            id_number=f"{random.randint(100000000000, 999999999999)}"
        )
        visitors.append(visitor)
    
    logger.info(f"Generated {len(visitors)} visitors")
    return visitors


def generate_fact_appointments(session, num_appointments=500):
    """Generate fact appointment records."""
    logger.info(f"Generating {num_appointments} appointment records...")
    
    # Get dimension IDs
    dates = session.query(DimDate).filter(DimDate.full_date >= date.today() - timedelta(days=90)).all()
    times = session.query(DimTime).all()
    doctors = session.query(DimDoctor).all()
    users = session.query(DimUser).all()
    diseases = session.query(DimDisease).all()
    
    statuses = ["Scheduled", "Completed", "Cancelled", "No-Show"]
    status_weights = [0.5, 0.35, 0.10, 0.05]
    
    payment_statuses = ["Pending", "Paid", "Refunded"]
    
    appointments = []
    for i in range(num_appointments):
        selected_date = random.choice(dates)
        selected_time = random.choice(times)
        selected_doctor = random.choice(doctors)
        selected_user = random.choice(users)
        selected_disease = random.choice(diseases)
        
        status = random.choices(statuses, weights=status_weights)[0]
        
        appointment = FactAppointment(
            date_id=selected_date.date_id,
            time_id=selected_time.time_id,
            doctor_id=selected_doctor.doctor_id,
            user_id=selected_user.user_id,
            disease_id=selected_disease.disease_id,
            status=status,
            duration_minutes=random.choice([30, 45, 60]),
            consultation_fee=selected_doctor.consultation_fee,
            payment_status=random.choice(payment_statuses) if status == "Completed" else "Pending",
            created_at=datetime.now() - timedelta(days=random.randint(0, 90)),
            completed_at=datetime.now() - timedelta(days=random.randint(0, 30)) if status == "Completed" else None,
            notes=f"Appointment for {selected_disease.disease_name}"
        )
        appointments.append(appointment)
    
    logger.info(f"Generated {len(appointments)} appointments")
    return appointments


def generate_fact_visitor_checkins(session, num_checkins=100):
    """Generate visitor check-in records."""
    logger.info(f"Generating {num_checkins} visitor check-in records...")
    
    dates = session.query(DimDate).filter(DimDate.full_date >= date.today() - timedelta(days=30)).all()
    times = session.query(DimTime).all()
    visitors = session.query(DimVisitor).all()
    
    checkins = []
    for i in range(num_checkins):
        selected_date = random.choice(dates)
        selected_time = random.choice(times)
        selected_visitor = random.choice(visitors)
        
        checkin_datetime = datetime.combine(selected_date.full_date, selected_time.time_value)
        duration = random.randint(15, 120)
        
        checkin = FactVisitorCheckIn(
            date_id=selected_date.date_id,
            time_id=selected_time.time_id,
            visitor_id=selected_visitor.visitor_id,
            checkin_time=checkin_datetime,
            checkout_time=checkin_datetime + timedelta(minutes=duration) if random.random() > 0.3 else None,
            duration_minutes=duration if random.random() > 0.3 else None,
            notes=f"Visit for {selected_visitor.purpose}"
        )
        checkins.append(checkin)
    
    logger.info(f"Generated {len(checkins)} visitor check-ins")
    return checkins


# ==================== MAIN POPULATION FUNCTION ====================

def main():
    """Main function to populate star schema database."""
    print("\n" + "="*70)
    print("🌟 STAR SCHEMA DATABASE POPULATION")
    print("="*70)
    
    # Create all tables
    logger.info("\n📊 Creating database tables...")
    Base.metadata.create_all(engine)
    logger.info("✓ Tables created successfully")
    
    session = Session()
    
    try:
        # Populate dimension tables
        logger.info("\n📅 Populating dimension tables...")
        
        # 1. Date dimension
        dates = generate_date_dimension()
        session.bulk_save_objects(dates)
        session.commit()
        logger.info("✓ Date dimension populated")
        
        # 2. Time dimension
        times = generate_time_dimension()
        session.bulk_save_objects(times)
        session.commit()
        logger.info("✓ Time dimension populated")
        
        # 3. Doctor dimension
        doctors = generate_doctor_dimension()
        session.bulk_save_objects(doctors)
        session.commit()
        logger.info("✓ Doctor dimension populated")
        
        # 4. User dimension
        users = generate_user_dimension()
        session.bulk_save_objects(users)
        session.commit()
        logger.info("✓ User dimension populated")
        
        # 5. Disease dimension
        diseases = generate_disease_dimension()
        session.bulk_save_objects(diseases)
        session.commit()
        logger.info("✓ Disease dimension populated")
        
        # 6. Visitor dimension
        visitors = generate_visitor_dimension()
        session.bulk_save_objects(visitors)
        session.commit()
        logger.info("✓ Visitor dimension populated")
        
        # Populate fact tables
        logger.info("\n📊 Populating fact tables...")
        
        # 7. Fact appointments
        appointments = generate_fact_appointments(session, num_appointments=500)
        session.bulk_save_objects(appointments)
        session.commit()
        logger.info("✓ Fact appointments populated")
        
        # 8. Fact visitor check-ins
        checkins = generate_fact_visitor_checkins(session, num_checkins=100)
        session.bulk_save_objects(checkins)
        session.commit()
        logger.info("✓ Fact visitor check-ins populated")
        
        # Print summary
        print("\n" + "="*70)
        print("✅ DATABASE POPULATION SUMMARY")
        print("="*70)
        print(f"📅 Date records:           {session.query(DimDate).count():,}")
        print(f"⏰ Time slots:             {session.query(DimTime).count():,}")
        print(f"👨‍⚕️ Doctors:                {session.query(DimDoctor).count():,}")
        print(f"👤 Users/Patients:         {session.query(DimUser).count():,}")
        print(f"🏥 Diseases:               {session.query(DimDisease).count():,}")
        print(f"👔 Visitors:               {session.query(DimVisitor).count():,}")
        print(f"📋 Appointments:           {session.query(FactAppointment).count():,}")
        print(f"🚪 Visitor Check-ins:      {session.query(FactVisitorCheckIn).count():,}")
        print("="*70)
        print(f"\n✅ Database created: {DATABASE_URL}")
        print("✅ All data populated successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during population: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
