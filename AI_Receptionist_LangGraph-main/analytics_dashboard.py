"""
Analytics Dashboard for AI Receptionist
Provides business intelligence using star schema database
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import (
    get_star_session,
    get_peak_appointment_hours,
    get_popular_doctors,
    get_appointment_stats_by_status,
    get_revenue_by_specialty
)
from models_star import (
    FactAppointment, DimDate, DimTime, DimDoctor, DimUser, DimDisease
)
from sqlalchemy import func


def show_analytics_dashboard():
    """Display comprehensive analytics dashboard."""
    
    st.title("📊 Analytics Dashboard")
    st.markdown("---")
    
    session = get_star_session()
    
    try:
        # Key Metrics Row
        st.subheader("📈 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_appointments = session.query(FactAppointment).count()
            st.metric("Total Appointments", f"{total_appointments:,}")
        
        with col2:
            completed = session.query(FactAppointment).filter_by(status='Completed').count()
            st.metric("Completed", f"{completed:,}")
        
        with col3:
            total_doctors = session.query(DimDoctor).count()
            st.metric("Active Doctors", f"{total_doctors:,}")
        
        with col4:
            total_patients = session.query(DimUser).count()
            st.metric("Registered Patients", f"{total_patients:,}")
        
        st.markdown("---")
        
        # Row 1: Peak Hours and Popular Doctors
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⏰ Peak Appointment Hours")
            peak_hours = get_peak_appointment_hours(session, limit=10)
            
            if peak_hours:
                df_peak = pd.DataFrame(peak_hours)
                fig = px.bar(
                    df_peak,
                    x='time_slot',
                    y='count',
                    color='period',
                    title="Appointments by Time Slot",
                    labels={'time_slot': 'Time Slot', 'count': 'Appointments'},
                    color_discrete_map={
                        'Morning': '#FFB6C1',
                        'Afternoon': '#87CEEB',
                        'Evening': '#DDA0DD'
                    }
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No appointment data available")
        
        with col2:
            st.subheader("👨‍⚕️ Top Doctors")
            popular_doctors = get_popular_doctors(session, limit=10)
            
            if popular_doctors:
                df_doctors = pd.DataFrame(popular_doctors)
                fig = px.bar(
                    df_doctors,
                    x='name',
                    y='total_appointments',
                    color='specialty',
                    title="Most Popular Doctors",
                    labels={'name': 'Doctor', 'total_appointments': 'Appointments'},
                    hover_data=['rating', 'avg_fee']
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No doctor data available")
        
        st.markdown("---")
        
        # Row 2: Status Distribution and Revenue
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Appointment Status Distribution")
            status_stats = get_appointment_stats_by_status(session)
            
            if status_stats:
                fig = go.Figure(data=[go.Pie(
                    labels=list(status_stats.keys()),
                    values=list(status_stats.values()),
                    hole=0.4,
                    marker_colors=['#90EE90', '#FFB6C1', '#FFD700', '#FF6B6B']
                )])
                fig.update_layout(
                    title="Appointment Status Breakdown",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No status data available")
        
        with col2:
            st.subheader("💰 Revenue by Specialty")
            revenue_data = get_revenue_by_specialty(session)
            
            if revenue_data:
                df_revenue = pd.DataFrame(revenue_data)
                fig = px.bar(
                    df_revenue,
                    x='specialty',
                    y='total_revenue',
                    title="Revenue Analysis by Specialty",
                    labels={'specialty': 'Specialty', 'total_revenue': 'Total Revenue (₹)'},
                    hover_data=['total_appointments', 'avg_fee'],
                    color='total_revenue',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No revenue data available")
        
        st.markdown("---")
        
        # Row 3: Disease Trends and Patient Demographics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏥 Top Diseases")
            disease_stats = session.query(
                DimDisease.disease_name,
                DimDisease.specialty,
                func.count(FactAppointment.appointment_id).label('count')
            ).join(
                FactAppointment, DimDisease.disease_id == FactAppointment.disease_id
            ).group_by(
                DimDisease.disease_id
            ).order_by(
                func.count(FactAppointment.appointment_id).desc()
            ).limit(10).all()
            
            if disease_stats:
                df_diseases = pd.DataFrame([
                    {'disease': d.disease_name, 'specialty': d.specialty, 'count': d.count}
                    for d in disease_stats
                ])
                fig = px.bar(
                    df_diseases,
                    x='disease',
                    y='count',
                    color='specialty',
                    title="Most Common Diseases",
                    labels={'disease': 'Disease', 'count': 'Cases'}
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No disease data available")
        
        with col2:
            st.subheader("👥 Patient Demographics")
            age_groups = session.query(
                func.case(
                    (DimUser.age < 18, 'Under 18'),
                    (DimUser.age < 30, '18-29'),
                    (DimUser.age < 50, '30-49'),
                    (DimUser.age < 65, '50-64'),
                    else_='65+'
                ).label('age_group'),
                func.count(DimUser.user_id).label('count')
            ).group_by('age_group').all()
            
            if age_groups:
                df_age = pd.DataFrame([
                    {'age_group': ag.age_group, 'count': ag.count}
                    for ag in age_groups
                ])
                fig = go.Figure(data=[go.Pie(
                    labels=df_age['age_group'],
                    values=df_age['count'],
                    hole=0.3
                )])
                fig.update_layout(
                    title="Patient Age Distribution",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No patient data available")
        
        st.markdown("---")
        
        # Row 4: Appointment Trends Over Time
        st.subheader("📅 Appointment Trends")
        
        # Get appointments by date
        date_trends = session.query(
            DimDate.full_date,
            DimDate.day_name,
            func.count(FactAppointment.appointment_id).label('count')
        ).join(
            FactAppointment, DimDate.date_id == FactAppointment.date_id
        ).group_by(
            DimDate.full_date, DimDate.day_name
        ).order_by(
            DimDate.full_date
        ).limit(90).all()
        
        if date_trends:
            df_trends = pd.DataFrame([
                {'date': dt.full_date, 'day': dt.day_name, 'appointments': dt.count}
                for dt in date_trends
            ])
            
            fig = px.line(
                df_trends,
                x='date',
                y='appointments',
                title="Daily Appointment Trends (Last 90 Days)",
                labels={'date': 'Date', 'appointments': 'Number of Appointments'},
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available")
        
        st.markdown("---")
        
        # Row 5: Detailed Tables
        st.subheader("📋 Detailed Reports")
        
        tab1, tab2, tab3 = st.tabs(["Doctor Performance", "Disease Statistics", "Revenue Details"])
        
        with tab1:
            doctor_performance = session.query(
                DimDoctor.name,
                DimDoctor.specialty,
                DimDoctor.experience_years,
                DimDoctor.rating,
                func.count(FactAppointment.appointment_id).label('total_appointments'),
                func.sum(func.case((FactAppointment.status == 'Completed', 1), else_=0)).label('completed'),
                func.avg(FactAppointment.consultation_fee).label('avg_fee')
            ).join(
                FactAppointment, DimDoctor.doctor_id == FactAppointment.doctor_id
            ).group_by(
                DimDoctor.doctor_id
            ).order_by(
                func.count(FactAppointment.appointment_id).desc()
            ).all()
            
            if doctor_performance:
                df_perf = pd.DataFrame([{
                    'Doctor': dp.name,
                    'Specialty': dp.specialty,
                    'Experience': f"{dp.experience_years} years",
                    'Rating': dp.rating,
                    'Total Appointments': dp.total_appointments,
                    'Completed': dp.completed,
                    'Completion Rate': f"{(dp.completed/dp.total_appointments*100):.1f}%",
                    'Avg Fee': f"₹{dp.avg_fee:.0f}"
                } for dp in doctor_performance])
                st.dataframe(df_perf, use_container_width=True, hide_index=True)
            else:
                st.info("No performance data available")
        
        with tab2:
            disease_details = session.query(
                DimDisease.disease_name,
                DimDisease.specialty,
                DimDisease.category,
                DimDisease.severity,
                func.count(FactAppointment.appointment_id).label('cases')
            ).join(
                FactAppointment, DimDisease.disease_id == FactAppointment.disease_id
            ).group_by(
                DimDisease.disease_id
            ).order_by(
                func.count(FactAppointment.appointment_id).desc()
            ).limit(20).all()
            
            if disease_details:
                df_disease = pd.DataFrame([{
                    'Disease': dd.disease_name,
                    'Specialty': dd.specialty,
                    'Category': dd.category,
                    'Severity': dd.severity,
                    'Total Cases': dd.cases
                } for dd in disease_details])
                st.dataframe(df_disease, use_container_width=True, hide_index=True)
            else:
                st.info("No disease statistics available")
        
        with tab3:
            revenue_details = session.query(
                DimDoctor.specialty,
                func.count(FactAppointment.appointment_id).label('appointments'),
                func.sum(func.case((FactAppointment.payment_status == 'Paid', FactAppointment.consultation_fee), else_=0)).label('revenue'),
                func.sum(func.case((FactAppointment.payment_status == 'Pending', FactAppointment.consultation_fee), else_=0)).label('pending'),
                func.avg(FactAppointment.consultation_fee).label('avg_fee')
            ).join(
                FactAppointment, DimDoctor.doctor_id == FactAppointment.doctor_id
            ).group_by(
                DimDoctor.specialty
            ).order_by(
                func.sum(func.case((FactAppointment.payment_status == 'Paid', FactAppointment.consultation_fee), else_=0)).desc()
            ).all()
            
            if revenue_details:
                df_rev = pd.DataFrame([{
                    'Specialty': rd.specialty,
                    'Appointments': rd.appointments,
                    'Revenue (Paid)': f"₹{rd.revenue:,.0f}",
                    'Pending': f"₹{rd.pending:,.0f}",
                    'Avg Fee': f"₹{rd.avg_fee:.0f}"
                } for rd in revenue_details])
                st.dataframe(df_rev, use_container_width=True, hide_index=True)
            else:
                st.info("No revenue details available")
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Analytics Dashboard - AI Receptionist",
        page_icon="📊",
        layout="wide"
    )
    show_analytics_dashboard()
