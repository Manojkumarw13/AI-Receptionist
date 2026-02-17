"""
Doctor Availability Calendar View
Interactive calendar showing doctor availability and appointments
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from database.connection import get_session
from database.models import Appointment, Doctor
from sqlalchemy import and_
import pandas as pd

def show_calendar_view():
    """Main calendar view page"""
    st.header("📅 Doctor Availability Calendar")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "Start Date", 
            datetime.now().date(),
            key="cal_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date", 
            (datetime.now() + timedelta(days=7)).date(),
            key="cal_end_date"
        )
    
    with col3:
        session = get_session()
        try:
            doctors = session.query(Doctor).all()
            doctor_names = ["All Doctors"] + [d.name for d in doctors]
            selected_doctor = st.selectbox(
                "Doctor", 
                doctor_names,
                key="cal_doctor_select"
            )
        finally:
            session.close()
    
    # Validate date range
    if start_date > end_date:
        st.error("Start date must be before end date")
        return
    
    # Display calendar
    if selected_doctor == "All Doctors":
        show_all_doctors_calendar(start_date, end_date)
    else:
        show_doctor_calendar(selected_doctor, start_date, end_date)


def show_doctor_calendar(doctor_name, start_date, end_date):
    """Show calendar for specific doctor"""
    session = get_session()
    
    try:
        # Fetch appointments
        appointments = session.query(Appointment).filter(
            and_(
                Appointment.doctor_name == doctor_name,
                Appointment.appointment_time >= datetime.combine(start_date, datetime.min.time()),
                Appointment.appointment_time <= datetime.combine(end_date, datetime.max.time()),
                Appointment.is_deleted == False
            )
        ).all()
        
        # Create visualization
        st.subheader(f"📊 Availability for {doctor_name}")
        
        # Heatmap
        fig = create_availability_heatmap(appointments, start_date, end_date, doctor_name)
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        show_statistics(appointments, start_date, end_date)
        
        # Appointment list
        show_appointment_list(appointments)
        
    finally:
        session.close()


def show_all_doctors_calendar(start_date, end_date):
    """Show calendar for all doctors"""
    session = get_session()
    
    try:
        # Fetch all appointments
        appointments = session.query(Appointment).filter(
            and_(
                Appointment.appointment_time >= datetime.combine(start_date, datetime.min.time()),
                Appointment.appointment_time <= datetime.combine(end_date, datetime.max.time()),
                Appointment.is_deleted == False
            )
        ).all()
        
        # Group by doctor
        doctors = session.query(Doctor).all()
        
        st.subheader("📊 All Doctors Availability")
        
        # Create summary chart
        fig = create_doctor_summary_chart(appointments, doctors, start_date, end_date)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show statistics
        show_statistics(appointments, start_date, end_date)
        
    finally:
        session.close()


def create_availability_heatmap(appointments, start_date, end_date, doctor_name):
    """Create Plotly heatmap of availability"""
    # Generate time slots (9 AM - 5 PM, 30 min intervals)
    dates_list = []
    times_list = []
    availability_list = []
    hover_text = []
    
    current_date = start_date
    while current_date <= end_date:
        for hour in range(9, 17):  # 9 AM to 5 PM
            for minute in [0, 30]:
                time_slot = f"{hour:02d}:{minute:02d}"
                slot_datetime = datetime.combine(
                    current_date, 
                    datetime.strptime(time_slot, "%H:%M").time()
                )
                
                # Check if slot is booked
                booked_apt = None
                for apt in appointments:
                    if apt.appointment_time == slot_datetime:
                        booked_apt = apt
                        break
                
                dates_list.append(current_date.strftime("%Y-%m-%d"))
                times_list.append(time_slot)
                
                if booked_apt:
                    availability_list.append(0)  # Booked
                    hover_text.append(
                        f"Date: {current_date.strftime('%Y-%m-%d')}<br>"
                        f"Time: {time_slot}<br>"
                        f"Status: BOOKED<br>"
                        f"Patient: {booked_apt.user_email}<br>"
                        f"Reason: {booked_apt.disease}"
                    )
                else:
                    availability_list.append(1)  # Available
                    hover_text.append(
                        f"Date: {current_date.strftime('%Y-%m-%d')}<br>"
                        f"Time: {time_slot}<br>"
                        f"Status: AVAILABLE"
                    )
        
        current_date += timedelta(days=1)
    
    # Create DataFrame for easier manipulation
    df = pd.DataFrame({
        'Date': dates_list,
        'Time': times_list,
        'Availability': availability_list,
        'Hover': hover_text
    })
    
    # Pivot for heatmap
    pivot_df = df.pivot(index='Time', columns='Date', values='Availability')
    hover_df = df.pivot(index='Time', columns='Date', values='Hover')
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale=[
            [0, '#FF6B6B'],  # Red for booked
            [1, '#51CF66']   # Green for available
        ],
        showscale=True,
        colorbar=dict(
            title="Status",
            tickvals=[0, 1],
            ticktext=['Booked', 'Available']
        ),
        hovertext=hover_df.values,
        hovertemplate='%{hovertext}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Availability Heatmap - {doctor_name}",
        xaxis_title="Date",
        yaxis_title="Time",
        height=600,
        xaxis=dict(tickangle=-45)
    )
    
    return fig


def create_doctor_summary_chart(appointments, doctors, start_date, end_date):
    """Create summary chart for all doctors"""
    # Count appointments per doctor
    doctor_counts = {}
    for doctor in doctors:
        count = sum(1 for apt in appointments if apt.doctor_name == doctor.name)
        doctor_counts[doctor.name] = count
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=list(doctor_counts.keys()),
            y=list(doctor_counts.values()),
            marker_color='#4CAF50',
            text=list(doctor_counts.values()),
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Appointments by Doctor",
        xaxis_title="Doctor",
        yaxis_title="Number of Appointments",
        height=400,
        xaxis=dict(tickangle=-45)
    )
    
    return fig


def show_statistics(appointments, start_date, end_date):
    """Show appointment statistics"""
    st.subheader("📈 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Appointments", len(appointments))
    
    with col2:
        scheduled = sum(1 for apt in appointments if apt.status == "Scheduled")
        st.metric("Scheduled", scheduled)
    
    with col3:
        completed = sum(1 for apt in appointments if apt.status == "Completed")
        st.metric("Completed", completed)
    
    with col4:
        cancelled = sum(1 for apt in appointments if apt.status == "Cancelled")
        st.metric("Cancelled", cancelled)
    
    # Calculate availability rate
    total_days = (end_date - start_date).days + 1
    total_slots = total_days * 16  # 16 slots per day (9 AM - 5 PM, 30 min intervals)
    booked_slots = len(appointments)
    availability_rate = ((total_slots - booked_slots) / total_slots) * 100 if total_slots > 0 else 0
    
    st.info(f"📊 Availability Rate: {availability_rate:.1f}% ({total_slots - booked_slots}/{total_slots} slots available)")


def show_appointment_list(appointments):
    """Show list of appointments"""
    st.subheader("📋 Scheduled Appointments")
    
    if not appointments:
        st.info("No appointments scheduled in this period")
        return
    
    # Sort by appointment time
    sorted_appointments = sorted(appointments, key=lambda x: x.appointment_time)
    
    for apt in sorted_appointments:
        status_emoji = {
            "Scheduled": "🟢",
            "Completed": "✅",
            "Cancelled": "❌"
        }.get(apt.status, "⚪")
        
        with st.expander(
            f"{status_emoji} {apt.appointment_time.strftime('%Y-%m-%d %H:%M')} - {apt.user_email}"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Doctor:** {apt.doctor_name}")
                st.write(f"**Disease:** {apt.disease}")
            with col2:
                st.write(f"**Status:** {apt.status}")
                st.write(f"**Created:** {apt.created_at.strftime('%Y-%m-%d')}")
