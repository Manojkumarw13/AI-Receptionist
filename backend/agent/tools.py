# FIXED Issue #9: Authentication Note
# The agent tools receive user_email as a parameter from the app context.
# The app.py handles authentication via st.session_state.authenticated
# and st.session_state.user_email. Tools should only be called when
# user is authenticated, and user_email should come from session state.
import os
import datetime
import smtplib
from email.mime.text import MIMEText
from langchain_core.tools import tool
import qrcode
import html  # FIXED Issue #59: For input sanitization
from utils.ml_predictor import appointment_predictor
from utils.logging_config import setup_logging
from database.connection import get_session
from database.models import Appointment, Visitor, Doctor
from config import (
    IMAGES_DIR, MAX_IMAGE_SIZE_BYTES, ALLOWED_IMAGE_TYPES,
    APPOINTMENT_SLOT_DURATION_MINUTES, AVAILABILITY_SEARCH_DAYS,
    WORKING_HOURS_START, WORKING_HOURS_END,  # FIXED Issue #41
    SMTP_SERVER, SMTP_PORT  # FIXED Issue #56
)
from utils.timezone_utils import now_with_timezone, get_timezone  # FIXED Issue #22, #38, #48
from sqlalchemy import and_
import time as time_module  # FIXED Issue #50: For timestamp generation
from pathlib import Path  # FIXED Issue #58: For directory validation

# Initialize logging using centralized config
logger = setup_logging(__name__)

# FIXED Issue #23: Image directory now from config
# IMAGES_DIR imported from config.py

# The directory creation is now handled by IMAGES_DIR.mkdir(parents=True, exist_ok=True)
# if not os.path.exists(IMAGES_DIR):
#     os.makedirs(IMAGES_DIR)


# FIXED Issue #59: Input sanitization helper
def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS attacks.
    
    Args:
        text: User input string to sanitize
    
    Returns:
        str: HTML-escaped and trimmed string
    """
    if not text:
        return text
    return html.escape(text.strip())


# Function to send email notifications
def send_email_notification(to_email: str, subject: str, message: str) -> bool:
    """Send an email notification.
    
    FIXED Issue #39: Added comprehensive docstring
    FIXED Issue #40: Added type hints
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
    
    Returns:
        bool: True if email sent successfully, False otherwise
    
    Note:
        Returns False instead of raising exceptions to prevent
        transaction rollbacks when email fails.
    """
    # FIXED Issue #56: Use SMTP config constants
    smtp_server = SMTP_SERVER
    smtp_port = SMTP_PORT
    from_email = os.getenv("EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    if not from_email or not password:
        logger.warning("Email credentials not configured. Skipping email notification.")
        return False

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            logger.info("Connecting to SMTP server...")
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
            logger.info(f"Email sent to {to_email} with subject: {subject}")
            return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# Tool to get the next available appointment
@tool
def get_next_available_appointment():
    """Returns the next available appointment within working hours.
    
    FIX BUG-13: Now respects WORKING_HOURS_START/END from config so it
    never suggests slots outside working hours or on weekends.
    """
    session = get_session()
    try:
        current_time = datetime.datetime.now()
        # Align to next 30 min slot
        minutes_to_add = 30 - current_time.minute % 30
        if minutes_to_add == 30:
            minutes_to_add = 0
        
        start_time = current_time + datetime.timedelta(minutes=minutes_to_add)
        start_time = start_time.replace(second=0, microsecond=0)
        
        # FIX BUG-13: Helper to advance to next valid working slot
        def advance_to_working_hours(dt):
            """Move dt to start of next working slot if outside working hours."""
            # Skip weekends (Mon=0 ... Sun=6)
            while dt.weekday() >= 5:  # Saturday or Sunday
                dt = (dt + datetime.timedelta(days=1)).replace(
                    hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0
                )
            # Before working hours: jump to start of working day
            if dt.hour < WORKING_HOURS_START:
                dt = dt.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)
            # After working hours: jump to next working day
            elif dt.hour >= WORKING_HOURS_END:
                dt = (dt + datetime.timedelta(days=1)).replace(
                    hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0
                )
                # Recurse to skip any weekend that follows
                dt = advance_to_working_hours(dt)
            return dt
        
        start_time = advance_to_working_hours(start_time)
        
        while True:
            # Check if slot is booked in database
            is_booked = session.query(Appointment).filter(
                Appointment.appointment_time == start_time,
                Appointment.is_deleted == False  # FIX: also ignore soft-deleted
            ).first() is not None
            
            if not is_booked:
                # Check ML prediction
                is_optimal, message = appointment_predictor.predict_availability(
                    start_time.strftime("%Y-%m-%d"), 
                    start_time.strftime("%H:%M"), 
                    30
                )
                
                if is_optimal:
                    logger.info(f"Next available appointment: {start_time}")
                    return {
                        "success": True,
                        "appointment_time": start_time.strftime("%Y-%m-%d %H:%M"),
                        "message": f"Next available appointment is at {start_time.strftime('%Y-%m-%d %H:%M')}"
                    }
            
            # Advance by 30 minutes, then re-check working hours
            start_time = advance_to_working_hours(
                start_time + datetime.timedelta(minutes=30)
            )
            # Limit search to avoid infinite loop
            if (start_time - current_time).days > 7:
                return {
                    "success": False,
                    "error": "NO_AVAILABILITY",
                    "message": "No appointments available in the next 7 days."
                }
    finally:
        session.close()


@tool
def check_availability_ml(date_str: str, time_str: str, duration: int = 30):
    """
    Checks if a specific time is available and optimal using ML.
    Args:
        date_str: 'YYYY-MM-DD'
        time_str: 'HH:MM'
        duration: duration in minutes (default 30)
    """
    available, message = appointment_predictor.predict_availability(date_str, time_str, duration)
    return f"Availability Status: {'Optimal' if available else 'High Risk'}. Details: {message}"


@tool
def generate_qr_code(appointment_details: str, filepath: str = None):
    """Generates a QR code for the appointment details.
    
    FIXED Issue #58: Added path validation and error handling
    FIXED Issue #57: Added comprehensive logging
    
    Args:
        appointment_details: Data to encode in QR code
        filepath: Optional custom filepath for QR code
    
    Returns:
        str: Success/error message
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(appointment_details)
        qr.make(fit=True)

        # Generate filepath if not provided
        if not filepath:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qr_{timestamp}.png"
            filepath = str(IMAGES_DIR / filename)
        
        # FIXED Issue #58: Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filepath)
        
        # FIXED Issue #57: Log successful operation
        logger.info(f"QR code generated successfully at {filepath}")
        return f"QR Code generated at {filepath}"
    except Exception as e:
        # FIXED Issue #58: Proper error handling
        logger.error(f"Failed to generate QR code: {e}")
        return f"Failed to generate QR code: {e}"


def validate_image_file(image_data: bytes) -> tuple[bool, str]:
    """Validate image file size and type.
    
    Args:
        image_data: Raw image bytes
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # FIXED Issue #24: File size validation
    if len(image_data) > MAX_IMAGE_SIZE_BYTES:
        return False, f"Image too large. Maximum size is {MAX_IMAGE_SIZE_BYTES // (1024*1024)}MB"
    
    # FIXED Issue #25: File type validation using magic bytes
    for mime_type, magic_bytes in ALLOWED_IMAGE_TYPES.items():
        if image_data.startswith(magic_bytes):
            return True, ""
    
    return False, "Invalid image format. Only JPEG, PNG, and GIF are allowed"


@tool
def register_visitor(name: str, purpose: str, company: str = None, image_data: bytes = None):
    """
    Registers a visitor and logs their entry.
    
    FIXED Issue #59: Added input sanitization
    FIXED Issue #57: Added comprehensive logging
    
    Args:
        name: Name of visitor
        purpose: Purpose of visit
        company: Company they represent
        image_data: (Optional) Bytes of the captured face image
    """
    session = get_session()
    try:
        # FIXED Issue #59: Sanitize all text inputs
        name = sanitize_input(name)
        purpose = sanitize_input(purpose)
        company = sanitize_input(company) if company else None
        
        check_in_time = datetime.datetime.now()
        image_path = None  # Initialize image_path to None
        
        # Save image if provided
        if image_data:
            # FIXED Issue #24, #25: Validate image before saving
            is_valid, error_msg = validate_image_file(image_data)
            if not is_valid:
                logger.warning(f"Invalid image upload attempt: {error_msg}")
                return f"Failed to register visitor: {error_msg}"
            
            try:
                # Create images directory if it doesn't exist
                IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                
                # Generate unique filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = str(IMAGES_DIR / f"visitor_{timestamp}.jpg")
                
                # Save image
                with open(image_path, "wb") as f:
                    f.write(image_data)
            except Exception as e:
                logger.error(f"Failed to save visitor image: {e}")
                return f"Failed to save visitor image: {e}"

        # Create visitor record in database
        visitor = Visitor(
            name=name,
            purpose=purpose,
            company=company,
            check_in_time=check_in_time,
            image_path=image_path if image_path else None
        )
        
        session.add(visitor)
        session.commit()
        
        # FIXED Issue #57: Comprehensive logging for successful operation
        logger.info(f"Visitor registered successfully: {name} from {company or 'N/A'} - Purpose: {purpose} at {check_in_time}")
        return f"Visitor {name} registered successfully at {check_in_time}."
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to register visitor: {e}")
        return f"Failed to register visitor: {e}"
    finally:
        session.close()


# Tool to book an appointment
@tool
def book_appointment(appointment_year: int, appointment_month: int, appointment_day: int,
                     appointment_hour: int, appointment_minute: int, 
                     doctor_name: str, disease: str, user_email: str):
    """Book an appointment at the specified time.
    
    FIXED Issue #60: Inputs sanitized to prevent XSS
    FIXED Issue #61: Handles DST edge cases
    
    Args:
        appointment_year: Year of appointment
        appointment_month: Month of appointment
        appointment_day: Day of appointment
        appointment_hour: Hour of appointment (0-23)
        appointment_minute: Minute of appointment (0-59)
        doctor_name: Name of the doctor (will be sanitized)
        disease: Disease/condition for appointment (will be sanitized)
        user_email: Email of the user booking the appointment (will be sanitized)
    
    Returns:
        dict: Success/error response with appointment details or error message
    
    Raises:
        None: All errors returned as dict with success=False
    """
    session = get_session()
    try:
        # FIXED Issue #60: Sanitize text inputs to prevent XSS
        doctor_name = sanitize_input(doctor_name)
        disease = sanitize_input(disease)
        user_email = sanitize_input(user_email)
        # FIXED Issue #48: Create timezone-aware datetime from the start
        tz = get_timezone()
        time = tz.localize(datetime.datetime(
            appointment_year, appointment_month, appointment_day,
            appointment_hour, appointment_minute
        ))
        # FIX BUG-N10: Strip timezone before storing in the naive SQLite DateTime column.
        # SQLite stores the value without tzinfo, so reading it back produces a naive
        # datetime.  Keeping it tz-aware here means the conflict query (== time) would
        # always miss because naive != aware.  We keep the aware `time` for all
        # *validation* comparisons above (past-date, working-hours) and strip it only
        # when writing to / querying the DB.
        time_naive = time.replace(tzinfo=None)
        
        # FIXED Issue #38, #48: Both datetimes are now timezone-aware
        if time < now_with_timezone():
            logger.warning(f"Attempt to book appointment in the past: {time}")
            # FIXED Issue #21: Standardized error format
            return {"success": False, "error": "PAST_DATE", "message": "Cannot book appointments in the past. Please select a future date and time."}
        
        # FIXED Issue #51: Validate working hours
        if not (WORKING_HOURS_START <= time.hour < WORKING_HOURS_END):
            logger.warning(f"Attempt to book outside working hours: {time.hour}:00")
            return {
                "success": False,
                "error": "OUTSIDE_WORKING_HOURS",
                "message": f"Appointments only available {WORKING_HOURS_START}:00 - {WORKING_HOURS_END}:00. Please select a time within business hours."
            }
        
        # FIXED: Validate doctor exists
        doctor = session.query(Doctor).filter_by(name=doctor_name).first()
        if not doctor:
            logger.warning(f"Attempt to book with non-existent doctor: {doctor_name}")
            # FIXED Issue #21: Standardized error format
            return {"success": False, "error": "DOCTOR_NOT_FOUND", "message": f"Doctor '{doctor_name}' not found. Please select a valid doctor."}
                                 
        # Check for conflicting appointments (slot already booked)
        # FIXED Issue #33: Exclude soft-deleted appointments
        # FIX BUG-N10: Use time_naive for DB queries — SQLite stores naive datetimes
        existing = session.query(Appointment).filter(
            and_(
                Appointment.appointment_time == time_naive,
                Appointment.is_deleted == False
            )
        ).first()
        
        if existing:
            logger.warning(f"Attempt to book already booked slot: {time}")
            # FIXED Issue #21: Standardized error format
            return {"success": False, "error": "SLOT_BOOKED", "message": f"Appointment at {time} is already booked. Please choose another time."}
        
        # FIXED: Check user doesn't have conflicting appointment
        # FIXED Issue #33: Exclude soft-deleted appointments
        # FIX BUG-N10: Use time_naive for DB queries
        user_conflict = session.query(Appointment).filter(
            and_(
                Appointment.user_email == user_email,
                Appointment.appointment_time == time_naive,
                Appointment.is_deleted == False
            )
        ).first()
        
        if user_conflict:
            logger.warning(f"User {user_email} already has appointment at {time}")
            # FIXED Issue #21: Standardized error format
            return {"success": False, "error": "USER_CONFLICT", "message": f"You already have an appointment at {time}. Cannot book multiple appointments at the same time."}
        
        # FIXED Issue #53: Check for duplicate appointment with same doctor on same day
        # FIX BUG-N10: Use time_naive for same-day range calculations
        same_day_start = time_naive.replace(hour=0, minute=0, second=0, microsecond=0)
        same_day_end = time_naive.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        existing_with_doctor = session.query(Appointment).filter(
            and_(
                Appointment.user_email == user_email,
                Appointment.doctor_name == doctor_name,
                Appointment.appointment_time >= same_day_start,
                Appointment.appointment_time <= same_day_end,
                Appointment.is_deleted == False
            )
        ).first()
        
        if existing_with_doctor:
            logger.warning(f"User {user_email} already has appointment with {doctor_name} on {time.date()}")
            return {
                "success": False,
                "error": "DUPLICATE_APPOINTMENT",
                "message": f"You already have an appointment with {doctor_name} today at {existing_with_doctor.appointment_time.strftime('%H:%M')}. Cannot book multiple appointments with the same doctor on the same day."
            }
        
        # Check ML Prediction
        is_safe, msg = appointment_predictor.predict_availability(
            time.strftime("%Y-%m-%d"), time.strftime("%H:%M"), 30
        )
        if not is_safe:
            # FIX BUG-11: Return consistent dict type instead of plain string
            return {
                "success": False,
                "error": "ML_WARNING",
                "message": f"Warning: {msg}. Please choose a different time slot."
            }

        # Add the appointment to database
        # FIX BUG-N10: Store time_naive so the DB column stays naive (SQLite strips tz anyway)
        new_appointment = Appointment(
            user_email=user_email,
            doctor_name=doctor_name,
            disease=disease,
            appointment_time=time_naive
        )
        
        session.add(new_appointment)
        session.commit()
        appointment_id = new_appointment.id
        logger.info(f"Appointment booked: {time} with {doctor_name}")
        
        # FIXED Issue #13: Email sending separated from transaction
        # FIXED Issue #35, #50: Generate and save QR code with proper timestamp
        # Use current time for timestamp to avoid timezone issues
        timestamp = int(time_module.time())
        qr_filename = f"appointment_{appointment_id}_{timestamp}.png"
        qr_path = str(IMAGES_DIR / qr_filename)
        qr_res = generate_qr_code(f"Appointment ID: {appointment_id}, Doctor: {doctor_name}, Time: {time}", qr_path)
        
        # Update appointment with QR code path
        new_appointment.qr_code_path = qr_path
        session.commit()
        
        # Send notification email (non-blocking, won't rollback transaction if fails)
        subject = "Appointment Confirmation"
        message = f"Your appointment with Dr. {doctor_name} for {disease} is booked for {time}. {qr_res}"
        
        email_sent = send_email_notification(user_email, subject, message)
        if email_sent:
            logger.info(f"Confirmation email sent to user: {user_email}")
            # FIXED Issue #21: Standardized success format
            return {"success": True, "appointment_id": appointment_id, "message": f"Appointment booked successfully for {time} with Dr. {doctor_name}. Confirmation email sent."}
        else:
            logger.warning(f"Appointment booked but email failed for: {user_email}")
            # FIXED Issue #21: Standardized success format
            return {"success": True, "appointment_id": appointment_id, "message": f"Appointment booked successfully for {time} with Dr. {doctor_name}. (Email notification failed - please check your email settings)"}
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to book appointment: {e}")
        # FIXED Issue #21: Standardized error format
        return {"success": False, "error": "BOOKING_FAILED", "message": f"Failed to book appointment: {str(e)}"}
    finally:
        session.close()


# Tool to cancel an appointment
@tool
def cancel_appointment(appointment_year: int, appointment_month: int, appointment_day: int,
                       appointment_hour: int, appointment_minute: int, user_email: str):
    """Cancel an appointment at the specified time.
    
    Args:
        appointment_year: Year of appointment
        appointment_month: Month of appointment
        appointment_day: Day of appointment
        appointment_hour: Hour of appointment
        appointment_minute: Minute of appointment
        user_email: Email of the user canceling the appointment
    """
    session = get_session()
    try:
        # FIXED Issue #48: Create timezone-aware datetime properly
        tz = get_timezone()
        time = tz.localize(datetime.datetime(
            appointment_year,
            appointment_month,
            appointment_day,
            appointment_hour,
            appointment_minute,
            0,  # second
            0   # microsecond
        ))
        
        appointment = session.query(Appointment).filter(
            and_(
                Appointment.appointment_time == time,
                Appointment.user_email == user_email
            )
        ).first()
        
        if appointment:
            # FIX BUG-12: Use soft delete instead of hard delete to preserve audit history
            appointment.is_deleted = True
            appointment.status = "Cancelled"
            session.commit()
            logger.info(f"Appointment at {time} soft-cancelled for user {user_email}")
            
            # FIXED Issue #13: Email sending separated from transaction
            subject = "Appointment Cancellation"
            message = f"Your appointment on {time} has been canceled."
            
            email_sent = send_email_notification(user_email, subject, message)
            if email_sent:
                logger.info(f"Cancellation email sent to user: {user_email}")
            else:
                logger.warning(f"Appointment cancelled but email failed for: {user_email}")
            
            # FIX BUG-N04: Return consistent dict type (was returning a plain string here,
            # but a dict on error — breaking any caller that checks result["success"])
            return {"success": True, "message": f"Appointment at {time} cancelled successfully."}
        else:
            logger.warning(f"No appointment found for user {user_email} at: {time}")
            # FIX BUG-N04: Return consistent dict type (was returning a plain string here)
            return {"success": False, "error": "NOT_FOUND", "message": f"No appointment found at {time} for your account"}
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to cancel appointment: {e}")
        return {"success": False, "error": "CANCELLATION_FAILED", "message": f"Failed to cancel appointment: {str(e)}"}
    finally:
        session.close()