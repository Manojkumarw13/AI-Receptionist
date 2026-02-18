import streamlit as st
import datetime
import os
import bcrypt  # FIXED: Changed from hashlib to bcrypt
import re  # FIXED: Added for email validation
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
import base64

# Database imports
from database.connection import init_db, check_db_exists, get_db_stats, get_session
from database.models import User, Visitor, Appointment, Doctor, DiseaseSpecialty
from agent.graph import caller_app, run_agent
from agent.tools import register_visitor, generate_qr_code
from ui.dashboard import show_analytics_dashboard
from utils.ml_predictor import appointment_predictor

# Load environment variables
load_dotenv()

# FIXED Issue #16: Validate required environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not GROQ_API_KEY:
    st.error("❌ CRITICAL: GROQ_API_KEY not set in .env file")
    st.info("Please create a .env file with: GROQ_API_KEY=your_api_key")
    st.stop()

if not EMAIL or not EMAIL_PASSWORD:
    st.warning("⚠️ Email credentials not configured. Email notifications will be disabled.")
    st.info("To enable emails, add EMAIL and EMAIL_PASSWORD to .env file")

# Initialize database
init_db()

st.set_page_config(
    page_title="AI Receptionist - Aura Health",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
LOGO_PATH = "assets/images/current/logo.png"
BACKGROUND_PATH = "assets/images/current/medical_technology.jpg"

# --- Helper Functions ---
def load_css():
    """Load custom CSS"""
    with open("assets/styles.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def get_base64_image(image_path):
    """Convert image to base64"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def display_logo():
    """Display app logo with enhanced styling"""
    if os.path.exists(LOGO_PATH):
        st.markdown("""
        <div class="logo-container">
            <img src="data:image/png;base64,{}" class="app-logo" alt="Aura Health Logo">
        </div>
        """.format(get_base64_image(LOGO_PATH)), unsafe_allow_html=True)

# --- Database & Auth Helpers ---
def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets strength requirements.
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # FIXED Issue #41: Use named constant
    from config import MIN_PASSWORD_LENGTH
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Valid"

# --- Session State Init ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_role" not in st.session_state:  # FIX BUG-04
    st.session_state.user_role = ""
if "user_name" not in st.session_state:  # FIX BUG-04
    st.session_state.user_name = ""
if "booking_step" not in st.session_state:
    st.session_state.booking_step = 1
if "selected_disease" not in st.session_state:
    st.session_state.selected_disease = ""
if "selected_doctor" not in st.session_state:
    st.session_state.selected_doctor = ""
if "booking_datetime" not in st.session_state:  # FIX BUG-22
    st.session_state.booking_datetime = None

# --- Authentication Logic ---
def login_page():
    # Load custom CSS
    load_css()
    
    # Background styling - using real medical image from Unsplash
    if os.path.exists(BACKGROUND_PATH):
        bg_base64 = get_base64_image(BACKGROUND_PATH)
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bg_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    # Center container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo
        display_logo()
        
        st.markdown("<h1 class='app-title'>Welcome to Aura Health AI</h1>", unsafe_allow_html=True)
        st.markdown("<p class='app-subtitle'>Your intelligent healthcare receptionist, available 24/7 🏥</p>", unsafe_allow_html=True)
        
        # Tabs for Login/Register
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
            email = st.text_input("Email Address", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button("🚀 Login", use_container_width=True):
                    session = get_session()
                    try:
                        user = session.query(User).filter_by(email=email).first()
                        if user and verify_password(password, user.password_hash):
                            # Check if account is active
                            if not user.is_active:
                                st.error("❌ Account is deactivated. Please contact admin.")
                            else:
                                # Update last login
                                user.last_login = datetime.datetime.now()
                                session.commit()
                                
                                # Set session state
                                st.session_state.authenticated = True
                                st.session_state.user_email = email
                                st.session_state.user_role = user.role
                                st.session_state.user_name = user.name or email.split('@')[0]
                                st.success("✅ Login successful! Redirecting...")
                                st.balloons()
                                st.rerun()
                        else:
                            st.error("❌ Invalid email or password.")
                    finally:
                        session.close()
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
            new_email = st.text_input("Email Address", key="register_email", placeholder="you@example.com")
            new_password = st.text_input("Password", type="password", key="register_password", placeholder="Create a strong password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", placeholder="Re-enter your password")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button("✨ Create Account", use_container_width=True):
                    # Validate email format
                    if not validate_email(new_email):
                        st.error("❌ Invalid email format")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match!")
                    # Validate password strength
                    elif not (is_valid := validate_password_strength(new_password))[0]:
                        st.error(f"❌ {is_valid[1]}")
                    else:
                        session = get_session()
                        try:
                            existing_user = session.query(User).filter_by(email=new_email).first()
                            if existing_user:
                                st.error("❌ User already exists. Please login.")
                            else:
                                new_user = User(email=new_email, password_hash=hash_password(new_password))
                                session.add(new_user)
                                session.commit()
                                st.success("✅ Registration successful! Please login.")
                                st.balloons()
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ Registration failed: {e}")
                        finally:
                            session.close()
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("<hr style='margin-top: 40px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #b8b8d1; font-size: 14px;'>🔒 Your data is secure and encrypted</p>", unsafe_allow_html=True)

# --- Tab 1: AI Assistant ---
def ai_assistant_page():
    st.markdown("## 🤖 AI Receptionist Agent")
    st.caption("💬 Chat with me to book appointments, check availability, or get assistance!")
    
    # Quick action buttons
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📅 Book Appointment", use_container_width=True):
            st.session_state.chat_history.append({
                "role": "user",
                "content": "I want to book an appointment"
            })
            st.rerun()
    
    with col2:
        if st.button("🔍 Check Availability", use_container_width=True):
            st.session_state.chat_history.append({
                "role": "user",
                "content": "Check doctor availability"
            })
            st.rerun()
    
    with col3:
        if st.button("👨‍⚕️ Find Doctor", use_container_width=True):
            st.session_state.chat_history.append({
                "role": "user",
                "content": "Help me find a doctor"
            })
            st.rerun()
    
    with col4:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    st.markdown("---")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for i, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
                st.markdown(message["content"])
        
        # Show typing indicator if processing
        if len(st.session_state.chat_history) > 0 and st.session_state.chat_history[-1]["role"] == "user":
            pass  # Streamlit handles this automatically

    # Chat input
    if prompt := st.chat_input("💭 Type your message here..."):
        # Add user message to state
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Get response from agent
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 Thinking..."):
                # Convert chat history to LangChain messages
                lc_history = []
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        lc_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        lc_history.append(AIMessage(content=msg["content"]))
                
                # Run agent with value history
                response_message = run_agent(lc_history)
                
                # If the response is an AIMessage object, extract content
                if hasattr(response_message, 'content'):
                    response_text = response_message.content
                else:
                    response_text = str(response_message)
                    
                st.markdown(response_text)
        
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
        st.rerun()

# --- Tab 2: Visitor Check-in ---
def visitor_checkin_page():
    st.markdown("## 📸 Visitor Check-in")
    st.caption("🔐 Register your visit for security and tracking purposes")
    
    # Recent check-ins
    with st.expander("📋 Recent Check-ins", expanded=False):
        session = get_session()
        try:
            visitors = session.query(Visitor).order_by(Visitor.check_in_time.desc()).limit(5).all()
            if visitors:
                for visitor in visitors:
                    st.markdown(f"**{visitor.name}** - {visitor.purpose} - {visitor.check_in_time.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.info("No recent check-ins")
        finally:
            session.close()
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 Visitor Information")
        name = st.text_input("👤 Full Name", placeholder="Enter your full name")
        company = st.text_input("🏢 Company / Organization", placeholder="Your organization")
        purpose = st.text_input("📌 Purpose of Visit", placeholder="Reason for your visit")
    
    with col2:
        st.markdown("### 📷 Photo Capture")
        img_file = st.camera_input("Take a photo")
        
        if img_file:
            st.success("✅ Photo captured!")

    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        if st.button("✅ Complete Check-in", use_container_width=True, type="primary"):
            if name and purpose:
                image_bytes = None
                if img_file is not None:
                    image_bytes = img_file.getvalue()
                
                result = register_visitor(name, purpose, company, image_bytes)
                st.success(f"🎉 {result}")
                st.balloons()
                
                # FIX BUG-02: Only clear visitor form fields, NOT auth state
                st.rerun()
            else:
                st.warning("⚠️ Please fill in Name and Purpose of Visit.")

# --- Tab 3: Manual Booking (Legacy + ML) ---
def manual_booking_page():
    st.markdown("## 📅 Book Appointment")
    st.caption("🏥 Schedule your appointment with our specialists")
    
    # Show upcoming appointments
    with st.expander("📋 Your Upcoming Appointments", expanded=False):
        session = get_session()
        try:
            user_appointments = session.query(Appointment).filter(
                Appointment.user_email == st.session_state.user_email,
                Appointment.appointment_time >= datetime.datetime.now()
            ).order_by(Appointment.appointment_time).all()
            
            if user_appointments:
                for apt in user_appointments:
                    st.markdown(f"""
                    <div class="glass-card" style="margin: 8px 0; padding: 16px;">
                        <strong>👨‍⚕️ Dr. {apt.doctor_name}</strong><br>
                        <span style="color: var(--accent-color);">📅 {apt.appointment_time.strftime('%Y-%m-%d %H:%M')}</span><br>
                        🏥 {apt.disease}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No upcoming appointments")
        finally:
            session.close()
    
    st.markdown("---")
    
    # Progress indicator
    progress_steps = ["Select Condition", "Choose Doctor", "Pick Date & Time", "Confirm"]
    current_step = st.session_state.booking_step
    
    st.markdown("### 📊 Booking Progress")
    progress_cols = st.columns(4)
    for i, step in enumerate(progress_steps, 1):
        with progress_cols[i-1]:
            if i < current_step:
                st.markdown(f"✅ **{step}**")
            elif i == current_step:
                st.markdown(f"🔵 **{step}**")
            else:
                st.markdown(f"⚪ {step}")
    
    st.progress((current_step - 1) / len(progress_steps))
    st.markdown("---")
    
    session = get_session()
    try:  # FIX BUG-01: Wrap session in try/finally to prevent leaks
        doctors = session.query(Doctor).all()
        disease_specialties_list = session.query(DiseaseSpecialty).all()
        disease_specialties = {ds.disease: ds.specialty for ds in disease_specialties_list}
    
        # Step 1: Select Condition
        if current_step == 1:
            st.markdown("### 🏥 Step 1: What brings you in today?")
            disease = st.text_input("Enter your condition or symptoms", placeholder="e.g., fever, headache, checkup", key="disease_input")
            
            if disease:
                st.session_state.selected_disease = disease
                specialty = disease_specialties.get(disease.lower())
                
                if specialty:
                    st.success(f"✅ Recommended Specialty: **{specialty}**")
                    if st.button("Next: Choose Doctor →", type="primary"):
                        st.session_state.booking_step = 2
                        st.rerun()
                else:
                    st.warning(f"⚠️ No specific specialty found for '{disease}'. Showing all doctors.")
                    if st.button("Continue Anyway →"):
                        st.session_state.booking_step = 2
                        st.rerun()
        
        # Step 2: Choose Doctor
        elif current_step == 2:
            st.markdown(f"### 👨‍⚕️ Step 2: Select Your Doctor")
            st.caption(f"Condition: **{st.session_state.selected_disease}**")
            
            disease = st.session_state.selected_disease
            specialty = disease_specialties.get(disease.lower())
            available_doctors = [d.name for d in doctors if d.specialty == specialty] if specialty else [d.name for d in doctors]
            
            if available_doctors:
                # Display doctors as cards
                cols = st.columns(2)
                for idx, doctor_name in enumerate(available_doctors):
                    doctor_info = next((d for d in doctors if d.name == doctor_name), None)
                    with cols[idx % 2]:
                        with st.container():
                            st.markdown(f"""
                            <div class="glass-card hover-lift" style="border: 1px solid var(--border-light);">
                                <h4>👨‍⚕️ Dr. {doctor_name}</h4>
                                <p><strong>Specialty:</strong> <span class="gradient-text">{doctor_info.specialty if doctor_info else 'General'}</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button(f"Select Dr. {doctor_name}", key=f"select_{doctor_name}", use_container_width=True):
                                st.session_state.selected_doctor = doctor_name
                                st.session_state.booking_step = 3
                                st.rerun()
            else:
                st.error("❌ No doctors available for this specialty")
            
            if st.button("← Back", key="back_to_step1"):
                st.session_state.booking_step = 1
                st.rerun()
        
        # Step 3: Pick Date & Time
        elif current_step == 3:
            st.markdown(f"### 📅 Step 3: Choose Date & Time")
            st.caption(f"Doctor: **Dr. {st.session_state.selected_doctor}** | Condition: **{st.session_state.selected_disease}**")
            
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("📅 Select Date", min_value=datetime.date.today(), value=datetime.date.today())
            with col2:
                time = st.time_input("🕐 Select Time", value=datetime.time(9, 0))
            
            st.markdown("---")
            
            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("← Back to Doctors", use_container_width=True):
                    st.session_state.booking_step = 2
                    st.rerun()
            
            with col_next:
                if st.button("Check Availability & Book →", use_container_width=True, type="primary"):
                    dt = datetime.datetime.combine(date, time)
                    
                    # ML Availability Check
                    with st.spinner("🔍 Checking availability..."):
                        is_optimal, ml_msg = appointment_predictor.predict_availability(
                            date.strftime("%Y-%m-%d"), 
                            time.strftime("%H:%M"), 
                            30
                        )
                    
                    if not is_optimal:
                        st.warning(f"⚠️ {ml_msg}")
                        if st.checkbox("📌 Book this slot anyway?"):
                            st.session_state.booking_step = 4
                            st.session_state.booking_datetime = dt
                            st.rerun()
                    else:
                        st.success("✅ This time slot looks great!")
                        st.session_state.booking_step = 4
                        st.session_state.booking_datetime = dt
                        st.rerun()
        
        # Step 4: Confirm Booking
        elif current_step == 4:
            st.markdown("### ✅ Step 4: Confirm Your Appointment")
            
            dt = st.session_state.booking_datetime
            
            # Summary card
            st.markdown(f"""
            <div class="glass-card">
                <h3 style='margin-top: 0;' class="gradient-text">📋 Appointment Summary</h3>
                <p><strong>👨‍⚕️ Doctor:</strong> Dr. {st.session_state.selected_doctor}</p>
                <p><strong>🏥 Condition:</strong> {st.session_state.selected_disease}</p>
                <p><strong>📅 Date & Time:</strong> {dt.strftime("%B %d, %Y at %I:%M %p")}</p>
                <p><strong>👤 Patient:</strong> {st.session_state.user_email}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            col_back, col_confirm = st.columns(2)
            
            with col_back:
                if st.button("← Back to Date Selection", use_container_width=True):
                    st.session_state.booking_step = 3
                    st.rerun()
            
            with col_confirm:
                if st.button("🎉 Confirm Booking", use_container_width=True, type="primary"):
                    booking_session = get_session()
                    try:
                        # FIX BUG-07: Conflict check now excludes soft-deleted appointments
                        conflict = booking_session.query(Appointment).filter(
                            Appointment.appointment_time == dt,
                            Appointment.is_deleted == False
                        ).first()
                        
                        if conflict:
                            st.error("❌ This slot is already booked. Please choose another time.")
                        else:
                            # FIX BUG-08: Success block is now correctly inside the else clause
                            new_appointment = Appointment(
                                user_email=st.session_state.user_email,
                                doctor_name=st.session_state.selected_doctor,
                                disease=st.session_state.selected_disease,
                                appointment_time=dt
                            )
                            booking_session.add(new_appointment)
                            booking_session.commit()
                            
                            st.success(f"✅ Appointment confirmed with Dr. {st.session_state.selected_doctor}!")
                            st.balloons()
                            
                            # QR Code Generation
                            qr_msg = generate_qr_code(f"Appointment: Dr. {st.session_state.selected_doctor} @ {dt}")
                            st.info(f"📱 {qr_msg}")
                            
                            # Reset booking flow
                            st.session_state.booking_step = 1
                            st.session_state.selected_disease = ""
                            st.session_state.selected_doctor = ""
                    except Exception as e:
                        booking_session.rollback()
                        st.error(f"❌ Booking failed: {e}")
                    finally:
                        booking_session.close()
    
    finally:  # FIX BUG-01: Ensure session always closes even on exception
        session.close()

# --- Sidebar Stats Dashboard ---
def display_stats():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    
    session = get_session()
    try:
        # User appointments
        user_appointments_count = session.query(Appointment).filter(
            Appointment.user_email == st.session_state.user_email
        ).count()
        
        # Total doctors
        doctors_count = session.query(Doctor).count()
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Your Appointments", user_appointments_count)
        with col2:
            st.metric("Available Doctors", doctors_count)
        
        # Total appointments today
        today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        today_end = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
        today_appointments_count = session.query(Appointment).filter(
            Appointment.appointment_time >= today_start,
            Appointment.appointment_time <= today_end
        ).count()
        st.sidebar.metric("Today's Appointments", today_appointments_count)
    finally:
        session.close()

# --- Main Layout ---
def main():
    # Load CSS
    load_css()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        with st.sidebar:
            # Logo in sidebar with enhanced styling
            logo_path = "static/images/current/logo.png"
            if os.path.exists(logo_path):
                logo_base64 = get_base64_image(logo_path)
                st.markdown(f"""
                <div style="text-align: center; padding: 10px;">
                    <img src="data:image/png;base64,{logo_base64}" class="sidebar-logo" alt="Aura Health">
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # User info
            st.markdown(f"""
            <div class="glass-card" style="padding: 16px; text-align: center;">
                <h3 style='margin: 0; font-size: 1.2rem;'>👤 {st.session_state.user_email.split('@')[0].title()}</h3>
                <p style='margin: 4px 0; color: var(--text-secondary); font-size: 14px;'>{st.session_state.user_email}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 🧭 Navigation")
            
            # Navigation with icons - conditional admin access
            nav_options = ["🤖 AI Assistant", "📸 Visitor Check-in", "📅 Manual Booking", "📊 Analytics Dashboard", "🗓️ Calendar View"]  # FIX BUG-05: distinct emoji
            
            # Add admin dashboard for admin users
            if st.session_state.get('user_role') == 'admin':
                nav_options.append("🔐 Admin Dashboard")
            
            page = st.radio(
                "Go to",
                nav_options,
                label_visibility="collapsed"
            )
            
            # Stats
            display_stats()
            
            st.markdown("---")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                # FIX BUG-03: Clear ALL auth-related session state on logout
                st.session_state.authenticated = False
                st.session_state.user_email = ""
                st.session_state.user_role = ""
                st.session_state.user_name = ""
                st.session_state.chat_history = []
                st.session_state.booking_step = 1
                st.session_state.selected_disease = ""
                st.session_state.selected_doctor = ""
                st.session_state.booking_datetime = None
                st.rerun()

        # Page routing
        if page == "🤖 AI Assistant":
            ai_assistant_page()
        elif page == "📸 Visitor Check-in":
            visitor_checkin_page()
        elif page == "📅 Manual Booking":
            manual_booking_page()
        elif page == "📊 Analytics Dashboard":  # FIX BUG-35: use already-imported function
            show_analytics_dashboard()
        elif page == "🗓️ Calendar View":  # FIX BUG-05: match updated emoji
            from ui.calendar_view import show_calendar_view
            show_calendar_view()
        elif page == "🔐 Admin Dashboard":
            from ui.admin_dashboard import show_admin_dashboard
            show_admin_dashboard()

if __name__ == "__main__":
    main()
