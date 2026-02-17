"""
Admin Dashboard for AI Receptionist
Provides administrative controls for user, doctor, and appointment management
Requires admin role for access
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.connection import get_session
from database.models import User, Doctor, Appointment, Visitor
from sqlalchemy import func, and_
import bcrypt

def check_admin_access():
    """Check if current user has admin role"""
    if 'user_role' not in st.session_state or st.session_state.user_role != 'admin':
        st.error("🚫 Access Denied: Admin privileges required")
        st.info("Please contact an administrator for access")
        st.stop()

def show_admin_dashboard():
    """Main admin dashboard page"""
    check_admin_access()
    
    st.title("🔐 Admin Dashboard")
    st.markdown("---")
    
    # Admin tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "👥 User Management",
        "👨‍⚕️ Doctor Management",
        "📅 Appointment Management",
        "📈 Analytics"
    ])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_doctor_management()
    
    with tab4:
        show_appointment_management()
    
    with tab5:
        show_analytics()


def show_overview():
    """Show admin dashboard overview"""
    st.subheader("📊 System Overview")
    
    session = get_session()
    try:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_users = session.query(User).count()
            st.metric("Total Users", total_users)
        
        with col2:
            total_doctors = session.query(Doctor).count()
            st.metric("Total Doctors", total_doctors)
        
        with col3:
            total_appointments = session.query(Appointment).count()
            st.metric("Total Appointments", total_appointments)
        
        with col4:
            total_visitors = session.query(Visitor).count()
            st.metric("Total Visitors", total_visitors)
        
        st.markdown("---")
        
        # Recent activity
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 Recent Appointments")
            recent_appointments = session.query(Appointment).order_by(
                Appointment.created_at.desc()
            ).limit(5).all()
            
            if recent_appointments:
                for apt in recent_appointments:
                    with st.expander(f"{apt.user_email} - {apt.doctor_name}"):
                        st.write(f"**Disease:** {apt.disease}")
                        st.write(f"**Time:** {apt.appointment_time.strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Status:** {apt.status}")
            else:
                st.info("No recent appointments")
        
        with col2:
            st.subheader("👥 Recent Users")
            recent_users = session.query(User).order_by(
                User.created_at.desc()
            ).limit(5).all()
            
            if recent_users:
                for user in recent_users:
                    role_emoji = {"admin": "🔐", "doctor": "👨‍⚕️", "user": "👤"}.get(user.role, "👤")
                    status_emoji = "🟢" if user.is_active else "🔴"
                    st.write(f"{role_emoji} {status_emoji} **{user.email}** ({user.role})")
            else:
                st.info("No recent users")
        
    finally:
        session.close()


def show_user_management():
    """User management interface"""
    st.subheader("👥 User Management")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("➕ Add New User", use_container_width=True):
            st.session_state.show_add_user = True
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Add user form
    if st.session_state.get('show_add_user', False):
        with st.form("add_user_form"):
            st.subheader("Add New User")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_name = st.text_input("Full Name")
            new_role = st.selectbox("Role", ["user", "admin", "doctor"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Add User", use_container_width=True):
                    if new_email and new_password:
                        add_user(new_email, new_password, new_name, new_role)
                        st.session_state.show_add_user = False
                        st.rerun()
                    else:
                        st.error("Email and password required")
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_add_user = False
                    st.rerun()
    
    # User list
    session = get_session()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        
        if users:
            # Create DataFrame for display
            user_data = []
            for user in users:
                user_data.append({
                    "ID": user.id,
                    "Email": user.email,
                    "Name": user.name or "N/A",
                    "Role": user.role,
                    "Active": "✅" if user.is_active else "❌",
                    "Created": user.created_at.strftime("%Y-%m-%d"),
                    "Last Login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
                })
            
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # User actions
            st.markdown("---")
            st.subheader("User Actions")
            
            selected_user_id = st.number_input("User ID", min_value=1, step=1)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Change Role", use_container_width=True):
                    new_role = st.selectbox("New Role", ["user", "admin", "doctor"], key="role_change")
                    if st.button("Confirm Role Change"):
                        change_user_role(selected_user_id, new_role)
            
            with col2:
                if st.button("🔒 Toggle Active Status", use_container_width=True):
                    toggle_user_status(selected_user_id)
            
            with col3:
                if st.button("🗑️ Delete User", use_container_width=True):
                    if st.button("⚠️ Confirm Delete", type="primary"):
                        delete_user(selected_user_id)
        else:
            st.info("No users found")
    
    finally:
        session.close()


def show_doctor_management():
    """Doctor management interface"""
    st.subheader("👨‍⚕️ Doctor Management")
    
    # Add doctor button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("➕ Add New Doctor", use_container_width=True):
            st.session_state.show_add_doctor = True
    
    # Add doctor form
    if st.session_state.get('show_add_doctor', False):
        with st.form("add_doctor_form"):
            st.subheader("Add New Doctor")
            doctor_name = st.text_input("Doctor Name")
            doctor_specialty = st.text_input("Specialty")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Add Doctor", use_container_width=True):
                    if doctor_name and doctor_specialty:
                        add_doctor(doctor_name, doctor_specialty)
                        st.session_state.show_add_doctor = False
                        st.rerun()
                    else:
                        st.error("Name and specialty required")
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_add_doctor = False
                    st.rerun()
    
    # Doctor list
    session = get_session()
    try:
        doctors = session.query(Doctor).order_by(Doctor.name).all()
        
        if doctors:
            # Group by specialty
            specialties = {}
            for doctor in doctors:
                if doctor.specialty not in specialties:
                    specialties[doctor.specialty] = []
                specialties[doctor.specialty].append(doctor)
            
            # Display by specialty
            for specialty, specialty_doctors in specialties.items():
                with st.expander(f"🏥 {specialty} ({len(specialty_doctors)} doctors)"):
                    for doctor in specialty_doctors:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"**Dr. {doctor.name}**")
                        with col2:
                            if st.button("✏️ Edit", key=f"edit_doc_{doctor.id}"):
                                st.session_state.edit_doctor_id = doctor.id
                        with col3:
                            if st.button("🗑️ Delete", key=f"del_doc_{doctor.id}"):
                                delete_doctor(doctor.id)
            
            # Edit doctor
            if 'edit_doctor_id' in st.session_state:
                doctor = session.query(Doctor).filter_by(id=st.session_state.edit_doctor_id).first()
                if doctor:
                    st.markdown("---")
                    with st.form("edit_doctor_form"):
                        st.subheader(f"Edit Dr. {doctor.name}")
                        new_name = st.text_input("Name", value=doctor.name)
                        new_specialty = st.text_input("Specialty", value=doctor.specialty)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Save Changes"):
                                update_doctor(doctor.id, new_name, new_specialty)
                                del st.session_state.edit_doctor_id
                                st.rerun()
                        with col2:
                            if st.form_submit_button("Cancel"):
                                del st.session_state.edit_doctor_id
                                st.rerun()
        else:
            st.info("No doctors found")
    
    finally:
        session.close()


def show_appointment_management():
    """Appointment management interface"""
    st.subheader("📅 Appointment Management")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Scheduled", "Completed", "Cancelled"])
    with col2:
        date_from = st.date_input("From Date", datetime.now().date() - timedelta(days=30))
    with col3:
        date_to = st.date_input("To Date", datetime.now().date() + timedelta(days=30))
    
    session = get_session()
    try:
        # Build query
        query = session.query(Appointment).filter(
            and_(
                Appointment.appointment_time >= datetime.combine(date_from, datetime.min.time()),
                Appointment.appointment_time <= datetime.combine(date_to, datetime.max.time())
            )
        )
        
        if status_filter != "All":
            query = query.filter(Appointment.status == status_filter)
        
        appointments = query.order_by(Appointment.appointment_time.desc()).all()
        
        if appointments:
            st.write(f"**Total:** {len(appointments)} appointments")
            
            # Display appointments
            for apt in appointments:
                status_color = {
                    "Scheduled": "🟢",
                    "Completed": "✅",
                    "Cancelled": "❌"
                }.get(apt.status, "⚪")
                
                with st.expander(
                    f"{status_color} {apt.appointment_time.strftime('%Y-%m-%d %H:%M')} - "
                    f"{apt.user_email} → Dr. {apt.doctor_name}"
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Patient:** {apt.user_email}")
                        st.write(f"**Doctor:** Dr. {apt.doctor_name}")
                        st.write(f"**Disease:** {apt.disease}")
                    with col2:
                        st.write(f"**Status:** {apt.status}")
                        st.write(f"**Created:** {apt.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**ID:** {apt.id}")
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Mark Completed", key=f"complete_{apt.id}"):
                            update_appointment_status(apt.id, "Completed")
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_{apt.id}"):
                            update_appointment_status(apt.id, "Cancelled")
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{apt.id}"):
                            delete_appointment(apt.id)
        else:
            st.info("No appointments found for selected filters")
    
    finally:
        session.close()


def show_analytics():
    """Show system analytics"""
    st.subheader("📈 System Analytics")
    
    session = get_session()
    try:
        # Time range selector
        time_range = st.selectbox("Time Range", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])
        
        days_map = {
            "Last 7 Days": 7,
            "Last 30 Days": 30,
            "Last 90 Days": 90,
            "All Time": 36500
        }
        days = days_map[time_range]
        start_date = datetime.now() - timedelta(days=days)
        
        # Appointments over time
        appointments = session.query(Appointment).filter(
            Appointment.created_at >= start_date
        ).all()
        
        if appointments:
            # Appointments by day
            df_apt = pd.DataFrame([
                {"Date": apt.created_at.date(), "Count": 1}
                for apt in appointments
            ])
            df_apt_grouped = df_apt.groupby("Date").sum().reset_index()
            
            fig1 = px.line(df_apt_grouped, x="Date", y="Count", title="Appointments Over Time")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Appointments by status
            status_counts = {}
            for apt in appointments:
                status_counts[apt.status] = status_counts.get(apt.status, 0) + 1
            
            fig2 = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Appointments by Status"
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Top doctors
            doctor_counts = {}
            for apt in appointments:
                doctor_counts[apt.doctor_name] = doctor_counts.get(apt.doctor_name, 0) + 1
            
            top_doctors = sorted(doctor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            fig3 = px.bar(
                x=[d[0] for d in top_doctors],
                y=[d[1] for d in top_doctors],
                title="Top 10 Doctors by Appointments",
                labels={"x": "Doctor", "y": "Appointments"}
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No data available for selected time range")
    
    finally:
        session.close()


# Helper functions
def add_user(email, password, name, role):
    """Add new user"""
    session = get_session()
    try:
        # Hash password
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        new_user = User(
            email=email,
            password_hash=hashed.decode('utf-8'),
            name=name,
            role=role
        )
        session.add(new_user)
        session.commit()
        st.success(f"✅ User {email} added successfully!")
    except Exception as e:
        session.rollback()
        st.error(f"❌ Error adding user: {e}")
    finally:
        session.close()


def change_user_role(user_id, new_role):
    """Change user role"""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.role = new_role
            session.commit()
            st.success(f"✅ User role changed to {new_role}")
            st.rerun()
        else:
            st.error("User not found")
    finally:
        session.close()


def toggle_user_status(user_id):
    """Toggle user active status"""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.is_active = not user.is_active
            session.commit()
            status = "activated" if user.is_active else "deactivated"
            st.success(f"✅ User {status}")
            st.rerun()
        else:
            st.error("User not found")
    finally:
        session.close()


def delete_user(user_id):
    """Delete user"""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            session.delete(user)
            session.commit()
            st.success("✅ User deleted")
            st.rerun()
        else:
            st.error("User not found")
    finally:
        session.close()


def add_doctor(name, specialty):
    """Add new doctor"""
    session = get_session()
    try:
        new_doctor = Doctor(name=name, specialty=specialty)
        session.add(new_doctor)
        session.commit()
        st.success(f"✅ Dr. {name} added successfully!")
    except Exception as e:
        session.rollback()
        st.error(f"❌ Error adding doctor: {e}")
    finally:
        session.close()


def update_doctor(doctor_id, name, specialty):
    """Update doctor"""
    session = get_session()
    try:
        doctor = session.query(Doctor).filter_by(id=doctor_id).first()
        if doctor:
            doctor.name = name
            doctor.specialty = specialty
            session.commit()
            st.success("✅ Doctor updated")
            st.rerun()
        else:
            st.error("Doctor not found")
    finally:
        session.close()


def delete_doctor(doctor_id):
    """Delete doctor"""
    session = get_session()
    try:
        doctor = session.query(Doctor).filter_by(id=doctor_id).first()
        if doctor:
            session.delete(doctor)
            session.commit()
            st.success("✅ Doctor deleted")
            st.rerun()
        else:
            st.error("Doctor not found")
    finally:
        session.close()


def update_appointment_status(apt_id, status):
    """Update appointment status"""
    session = get_session()
    try:
        apt = session.query(Appointment).filter_by(id=apt_id).first()
        if apt:
            apt.status = status
            session.commit()
            st.success(f"✅ Appointment marked as {status}")
            st.rerun()
        else:
            st.error("Appointment not found")
    finally:
        session.close()


def delete_appointment(apt_id):
    """Delete appointment"""
    session = get_session()
    try:
        apt = session.query(Appointment).filter_by(id=apt_id).first()
        if apt:
            session.delete(apt)
            session.commit()
            st.success("✅ Appointment deleted")
            st.rerun()
        else:
            st.error("Appointment not found")
    finally:
        session.close()
