# Authentication and Security Documentation

## Authentication Flow

### User Authentication (Issue #9)

The AI Receptionist application uses **session-based authentication** managed by Streamlit's session state.

#### How It Works:

1. **Login Process** ([app.py](file:///P:/Project/MINI%20PROJECT/AI%20RESEPTIONIST/AI_Receptionist_LangGraph-main/app.py#L112-L125))

   ```python
   if user and verify_password(password, user.password_hash):
       st.session_state.authenticated = True
       st.session_state.user_email = email
   ```

2. **Session State Variables:**
   - `st.session_state.authenticated` - Boolean flag indicating if user is logged in
   - `st.session_state.user_email` - Email of the authenticated user

3. **Protected Routes:**
   All main application features check authentication:
   ```python
   if not st.session_state.get("authenticated", False):
       show_login_page()
       return
   ```

#### Agent Tools Security:

**Design Decision:** Agent tools receive `user_email` as a parameter from the authenticated session context.

- ✅ Tools are **only called** when user is authenticated
- ✅ `user_email` parameter comes from `st.session_state.user_email`
- ✅ Tools validate user ownership (e.g., can only cancel own appointments)

**Example:**

```python
# In app.py - only called if authenticated
user_email = st.session_state.user_email
result = book_appointment(..., user_email=user_email)
```

**Security Measures:**

1. Tools validate user owns the resource (appointments)
2. Database queries filter by user_email
3. No hardcoded user emails
4. Session timeout handled by Streamlit

#### Rate Limiting (Issue #15)

**Current Status:** ⚠️ Not implemented

**Recommendation:**

- Use Streamlit's built-in session management
- Implement custom rate limiting with Redis/Memcached for production
- Add CAPTCHA for registration/login after failed attempts

**Simple Implementation:**

```python
# In app.py
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
    st.session_state.last_attempt = datetime.now()

# On failed login:
st.session_state.login_attempts += 1
if st.session_state.login_attempts > 5:
    st.error("Too many failed attempts. Please try again in 15 minutes.")
    st.stop()
```

---

## Environment Variables (Issue #16)

### Required Variables:

1. **GROQ_API_KEY** (CRITICAL)
   - Used for AI agent functionality
   - App will not start without this

2. **EMAIL** (Optional)
   - SMTP email for sending notifications
   - App warns if missing but continues

3. **EMAIL_PASSWORD** (Optional)
   - SMTP password
   - App warns if missing but continues

### Validation:

Environment variables are validated at startup ([app.py](file:///P:/Project/MINI%20PROJECT/AI%20RESEPTIONIST/AI_Receptionist_LangGraph-main/app.py#L21-L33)):

```python
if not GROQ_API_KEY:
    st.error("❌ CRITICAL: GROQ_API_KEY not set in .env file")
    st.stop()

if not EMAIL or not EMAIL_PASSWORD:
    st.warning("⚠️ Email credentials not configured.")
```

---

## Logging Configuration (Issue #17)

### Centralized Logging:

All modules now use centralized logging from [utils/logging_config.py](file:///P:/Project/MINI%20PROJECT/AI%20RESEPTIONIST/AI_Receptionist_LangGraph-main/utils/logging_config.py):

```python
from utils.logging_config import setup_logging

logger = setup_logging(__name__)
```

### Features:

- ✅ Consistent formatting across all modules
- ✅ Both console and file logging
- ✅ Logs saved to `logs/app.log`
- ✅ Configurable log levels
- ✅ No configuration conflicts

---

## Transaction Handling (Issue #13)

### Email Sending Separated from Transactions:

**Problem:** If email sending failed, the database transaction would rollback, but the error message was confusing.

**Solution:** Email sending is now separate from database transactions:

```python
# 1. Complete database transaction
session.add(new_appointment)
session.commit()
logger.info("Appointment booked")

# 2. Send email separately (non-blocking)
email_sent = send_email_notification(user_email, subject, message)
if email_sent:
    return "Appointment booked. Email sent."
else:
    return "Appointment booked. (Email failed - check settings)"
```

**Benefits:**

- ✅ Appointment is saved even if email fails
- ✅ Clear user feedback about email status
- ✅ No confusing "appointment failed" when it actually succeeded
- ✅ Email failures logged but don't break booking flow

---

## Database Optimization (Issue #18)

### Indexes Added:

**Appointment Table:**

- `idx_user_time` - Composite index on (user_email, appointment_time)
- `idx_doctor_time` - Composite index on (doctor_name, appointment_time)
- `idx_appointment_time` - **NEW** Standalone index on appointment_time

**Benefits:**

- ✅ Faster time-based queries
- ✅ Improved performance for availability checks
- ✅ Better query optimization for date range searches

---

## Security Best Practices

### Implemented:

- ✅ bcrypt password hashing (12 rounds)
- ✅ Email format validation
- ✅ Strong password requirements (8+ chars, mixed case, numbers)
- ✅ Session-based authentication
- ✅ User ownership validation
- ✅ Input validation (dates, doctors, conflicts)
- ✅ Environment variable validation
- ✅ SQL injection prevention (ORM only)

### Recommended for Production:

- ⚠️ Add HTTPS/TLS
- ⚠️ Implement rate limiting
- ⚠️ Add CAPTCHA
- ⚠️ Session timeout configuration
- ⚠️ Password reset functionality
- ⚠️ Two-factor authentication
- ⚠️ Audit logging
- ⚠️ IP whitelisting for admin functions

---

**Last Updated:** 2026-02-17  
**Version:** 1.0
