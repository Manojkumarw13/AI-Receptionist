# API Documentation

## Overview

The AI Receptionist application provides several key functionalities through its agent-based system. While there is no REST API currently, this document describes the available tools and their interfaces.

## FIXED Issue #45: API Documentation

### Current Architecture

The application uses a **LangGraph agent** with tool-based interactions rather than traditional REST endpoints.

---

## Available Tools

### 1. Book Appointment

**Tool Name:** `book_appointment`

**Description:** Books a medical appointment with a doctor.

**Parameters:**

- `appointment_year` (int): Year of appointment
- `appointment_month` (int): Month (1-12)
- `appointment_day` (int): Day of month
- `appointment_hour` (int): Hour (0-23)
- `appointment_minute` (int): Minute (0-59)
- `doctor_name` (str): Name of the doctor
- `disease` (str): Medical condition/reason for visit
- `user_email` (str): Email of the patient

**Returns:**

```python
{
    "success": True,
    "appointment_id": 123,
    "message": "Appointment booked successfully..."
}
```

**Error Codes:**

- `PAST_DATE`: Attempted to book in the past
- `DOCTOR_NOT_FOUND`: Invalid doctor name
- `SLOT_BOOKED`: Time slot already taken
- `USER_CONFLICT`: User has conflicting appointment
- `BOOKING_FAILED`: General failure

**Example:**

```python
result = book_appointment(
    appointment_year=2026,
    appointment_month=2,
    appointment_day=20,
    appointment_hour=10,
    appointment_minute=30,
    doctor_name="Dr. Smith",
    disease="Fever",
    user_email="patient@example.com"
)
```

---

### 2. Cancel Appointment

**Tool Name:** `cancel_appointment`

**Description:** Cancels an existing appointment (soft delete).

**Parameters:**

- `appointment_year` (int): Year of appointment
- `appointment_month` (int): Month (1-12)
- `appointment_day` (int): Day of month
- `appointment_hour` (int): Hour (0-23)
- `appointment_minute` (int): Minute (0-59)
- `user_email` (str): Email of the patient

**Returns:**

```python
{
    "success": True,
    "message": "Appointment cancelled successfully"
}
```

**Error Codes:**

- `NOT_FOUND`: Appointment not found
- `CANCELLATION_FAILED`: General failure

---

### 3. Get Next Available Appointment

**Tool Name:** `get_next_available_appointment`

**Description:** Finds the next available appointment slot.

**Parameters:**

- `doctor_name` (str, optional): Specific doctor name
- `disease` (str, optional): Medical condition

**Returns:**

```python
"One appointment available at 2026-02-20 10:30:00"
```

---

### 4. Register Visitor

**Tool Name:** `register_visitor`

**Description:** Registers a visitor check-in.

**Parameters:**

- `name` (str): Visitor name
- `purpose` (str): Purpose of visit
- `company` (str, optional): Company name
- `image_data` (bytes, optional): Photo (max 5MB, JPEG/PNG/GIF)

**Returns:**

```python
"Visitor {name} registered successfully at {time}"
```

**Validation:**

- Max file size: 5MB
- Allowed formats: JPEG, PNG, GIF
- Magic byte validation

---

## Response Format

All tools return standardized responses:

**Success:**

```python
{
    "success": True,
    "data": {...},  # Optional
    "message": "Human-readable message"
}
```

**Error:**

```python
{
    "success": False,
    "error": "ERROR_CODE",
    "message": "Human-readable error message"
}
```

---

## Authentication

**Method:** Session-based authentication via Streamlit

**Flow:**

1. User logs in via web interface
2. Session state stores `authenticated` flag and `user_email`
3. Tools receive `user_email` from session context
4. Tools validate user ownership of resources

**Security:**

- bcrypt password hashing (12 rounds)
- Email format validation
- Password strength requirements
- Session timeout (managed by Streamlit)

---

## Database Schema

### Operational Database (SQLite)

**Tables:**

- `users` - User accounts
- `appointments` - Appointment records
- `visitors` - Visitor check-ins
- `doctors` - Doctor information

**Key Fields:**

- `appointments.status`: Scheduled, Cancelled, Completed, No-Show
- `appointments.is_deleted`: Soft delete flag
- `appointments.qr_code_path`: QR code file path

### Analytics Database (Star Schema)

**Dimensions:**

- `dim_user` - Patient demographics
- `dim_doctor` - Doctor details
- `dim_disease` - Disease information
- `dim_date` - Date dimension
- `dim_time` - Time dimension

**Facts:**

- `fact_appointment` - Appointment facts
- `fact_visitor_check_in` - Visitor facts

---

## Configuration

**Environment Variables:**

- `GROQ_API_KEY` (required) - AI model API key
- `EMAIL` (optional) - SMTP email
- `EMAIL_PASSWORD` (optional) - SMTP password
- `TIMEZONE` (optional) - Default: Asia/Kolkata
- `DATABASE_URL` (optional) - Database connection string

**Constants:**

- `APPOINTMENT_SLOT_DURATION_MINUTES`: 30
- `AVAILABILITY_SEARCH_DAYS`: 7
- `WORKING_HOURS_START`: 9 (9 AM)
- `WORKING_HOURS_END`: 17 (5 PM)
- `MAX_IMAGE_SIZE_MB`: 5
- `MIN_PASSWORD_LENGTH`: 8

---

## Future REST API (Planned)

### Proposed Endpoints

**POST /api/appointments**

- Create new appointment
- Requires authentication

**GET /api/appointments**

- List user's appointments
- Supports pagination

**DELETE /api/appointments/{id}**

- Cancel appointment
- Soft delete

**GET /api/doctors**

- List available doctors
- Filter by specialty

**GET /api/availability**

- Check available slots
- Query parameters: doctor, date range

**POST /api/auth/login**

- User authentication
- Returns JWT token

**POST /api/auth/register**

- User registration
- Email verification

### Implementation Recommendations

**Framework:** FastAPI or Flask-RESTful

**Authentication:** JWT tokens

**Documentation:** Auto-generated Swagger/OpenAPI

**Rate Limiting:** Redis-based

**Example FastAPI Implementation:**

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AI Receptionist API")

class AppointmentCreate(BaseModel):
    doctor_name: str
    disease: str
    appointment_time: datetime

@app.post("/api/appointments")
async def create_appointment(
    appointment: AppointmentCreate,
    user: User = Depends(get_current_user)
):
    result = book_appointment(
        user_email=user.email,
        **appointment.dict()
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
```

---

## Health Check (Issue #47)

### Current Status

No dedicated health check endpoint exists.

### Recommended Implementation

**Streamlit App:**

```python
# Add to app.py
def health_check() -> dict:
    """Check application health."""
    checks = {
        "database": check_database_connection(),
        "ai_service": check_groq_api(),
        "email": check_smtp_connection(),
    }

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }

# Expose via query parameter
if st.query_params.get("health"):
    st.json(health_check())
    st.stop()
```

**FastAPI (Future):**

```python
@app.get("/health")
async def health():
    return health_check()

@app.get("/health/ready")
async def readiness():
    # Check if app is ready to serve requests
    return {"ready": True}

@app.get("/health/live")
async def liveness():
    # Check if app is alive
    return {"alive": True}
```

---

**Last Updated:** 2026-02-17  
**Version:** 1.0.0  
**Status:** Documentation complete
