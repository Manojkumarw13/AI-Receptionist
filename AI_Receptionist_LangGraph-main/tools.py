import os
import datetime
import smtplib
from email.mime.text import MIMEText
import logging
from langchain_core.tools import tool
import qrcode
from ml_utils import appointment_predictor
from database import get_session
from models import Appointment, Visitor
from sqlalchemy import and_

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Path for images
IMAGES_DIR = "static/images"

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)


# Function to send email notifications
def send_email_notification(to_email, subject, message):
    """Send an email notification."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = os.getenv("EMAIL")  # Your email
    password = os.getenv("EMAIL_PASSWORD")  # Email password

    if not from_email or not password:
        logging.error("EMAIL or EMAIL_PASSWORD environment variables are not set.")
        # Proceeding without error for demo purposes if creds are missing
        return

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            logging.info("Connecting to SMTP server...")
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
            logging.info(f"Email sent to {to_email} with subject: {subject}")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
        # Not raising error to avoid breaking agent flow


# Tool to get the next available appointment
@tool
def get_next_available_appointment():
    """Returns the next available appointment."""
    session = get_session()
    try:
        current_time = datetime.datetime.now()
        # Align to next 30 min slot
        minutes_to_add = 30 - current_time.minute % 30
        if minutes_to_add == 30: 
            minutes_to_add = 0
        
        start_time = current_time + datetime.timedelta(minutes=minutes_to_add)
        # Ensure seconds/microseconds are zero for cleaner matching
        start_time = start_time.replace(second=0, microsecond=0)
        
        while True:
            # Check if slot is booked in database
            is_booked = session.query(Appointment).filter(
                Appointment.appointment_time == start_time
            ).first() is not None
            
            if not is_booked:
                # Check ML prediction
                is_optimal, message = appointment_predictor.predict_availability(
                    start_time.strftime("%Y-%m-%d"), 
                    start_time.strftime("%H:%M"), 
                    30
                )
                
                if is_optimal:
                    logging.info(f"Next available appointment: {start_time}")
                    return f"One appointment available at {start_time}"
                
            start_time += datetime.timedelta(minutes=30)
            # Limit search to avoid infinite loop
            if (start_time - current_time).days > 7:
                return "No appointments available in the next 7 days."
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
def generate_qr_code(appointment_details: str):
    """Generates a QR code for the appointment details."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(appointment_details)
    qr.make(fit=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"qr_{timestamp}.png"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    return f"QR Code generated at {filepath}"


@tool
def register_visitor(name: str, purpose: str, company: str, image_data: bytes = None):
    """
    Registers a visitor and logs their entry.
    Args:
        name: Name of visitor
        purpose: Purpose of visit
        company: Company they represent
        image_data: (Optional) Bytes of the captured face image
    """
    session = get_session()
    try:
        check_in_time = datetime.datetime.now()
        image_path = ""
        
        if image_data:
            filename = f"{name}_{check_in_time.strftime('%Y%m%d_%H%M%S')}.jpg"
            image_path = os.path.join(IMAGES_DIR, filename)
            try:
                with open(image_path, "wb") as f:
                    f.write(image_data)
            except Exception as e:
                logging.error(f"Failed to save visitor image: {e}")

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
        
        logging.info(f"Visitor {name} registered at {check_in_time}")
        return f"Visitor {name} registered successfully at {check_in_time}."
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to register visitor: {e}")
        return f"Failed to register visitor: {e}"
    finally:
        session.close()


# Tool to book an appointment
@tool
def book_appointment(appointment_year: int, appointment_month: int, appointment_day: int,
                     appointment_hour: int, appointment_minute: int, appointment_name: str):
    """Book an appointment at the specified time."""
    session = get_session()
    try:
        time = datetime.datetime(appointment_year, appointment_month, appointment_day, 
                                 appointment_hour, appointment_minute)
                                 
        # Check for conflicting appointments
        existing = session.query(Appointment).filter(
            Appointment.appointment_time == time
        ).first()
        
        if existing:
            logging.warning(f"Attempt to book already booked slot: {time}")
            return f"Appointment at {time} is already booked"
        
        # Check ML Prediction
        is_safe, msg = appointment_predictor.predict_availability(
            time.strftime("%Y-%m-%d"), time.strftime("%H:%M"), 30
        )
        if not is_safe:
            return f"Warning: {msg}. Do you still want to proceed?"

        # Add the appointment to database
        # Note: This simplified version uses appointment_name as both user_email and doctor_name
        # In production, you'd want to pass these separately
        new_appointment = Appointment(
            user_email="user@example.com",  # Should be passed from session/context
            doctor_name=appointment_name,
            disease="general",  # Should be passed as parameter
            appointment_time=time
        )
        
        session.add(new_appointment)
        session.commit()
        
        logging.info(f"Appointment booked: {time} with {appointment_name}")
        
        # Generate QR
        qr_res = generate_qr_code(f"Appointment: {appointment_name} at {time}")
        
        # Send notifications
        subject = "Appointment Confirmation"
        message = f"Your appointment with {appointment_name} is booked for {time}. {qr_res}"
        
        try:
            user_email = "user@example.com"  # Replace with dynamic user email retrieval
            send_email_notification(user_email, subject, message)
            logging.info(f"Confirmation email sent to user: {user_email}")
        except Exception as e:
            logging.error(f"Failed to send email notifications: {e}")
            return f"Appointment booked, but email notification failed: {e}"
        
        return f"Appointment booked for {time}. {qr_res}"
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to book appointment: {e}")
        return f"Failed to book appointment: {e}"
    finally:
        session.close()


# Tool to cancel an appointment
@tool
def cancel_appointment(appointment_year: int, appointment_month: int, appointment_day: int,
                       appointment_hour: int, appointment_minute: int):
    """Cancel an appointment at the specified time."""
    session = get_session()
    try:
        time = datetime.datetime(appointment_year, appointment_month, appointment_day,
                                 appointment_hour, appointment_minute)
        
        appointment = session.query(Appointment).filter(
            Appointment.appointment_time == time
        ).first()
        
        if appointment:
            session.delete(appointment)
            session.commit()
            logging.info(f"Appointment canceled: {time}")
            
            # Notify user
            subject = "Appointment Cancellation"
            message = f"Your appointment on {time} has been canceled."
            
            try:
                user_email = "user@example.com"  # Replace with dynamic user email retrieval
                send_email_notification(user_email, subject, message)
                logging.info(f"Cancellation email sent to user: {user_email}")
            except Exception as e:
                logging.error(f"Failed to send cancellation email notifications: {e}")
                return f"Appointment canceled, but email notification failed: {e}"
            
            return f"Appointment at {time} cancelled"
        else:
            logging.warning(f"No appointment found to cancel at: {time}")
            return f"No appointment found at {time}"
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to cancel appointment: {e}")
        return f"Failed to cancel appointment: {e}"
    finally:
        session.close()