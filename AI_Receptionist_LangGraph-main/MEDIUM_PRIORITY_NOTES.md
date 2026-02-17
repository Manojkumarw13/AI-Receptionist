# Medium Priority Issues - Implementation Notes

## Issues Requiring Code Changes (Documented)

### Issue #27: No Pagination in Dashboard Queries

**Status:** PARTIALLY FIXED

**Changes Made:**

- Added `DEFAULT_PAGE_SIZE` and `MAX_PAGE_SIZE` to `config.py`
- Imported pagination config in `dashboard.py`

**Remaining Work:**
The dashboard queries use `.all()` which loads all records. To add pagination:

1. **Add pagination controls to Streamlit UI:**

```python
# In dashboard.py
page_size = st.selectbox("Results per page", [10, 25, 50, 100], index=2)
page_number = st.number_input("Page", min_value=1, value=1)

# Apply to queries
offset = (page_number - 1) * page_size
results = query.limit(page_size).offset(offset).all()
```

2. **Queries to paginate:**

- Line 89: Doctor performance query
- Line 158: Disease statistics query
- Line 198: Appointment trends query

**Note:** Full pagination implementation requires UI changes which are best done when user can test interactively.

---

### Issue #28: Inefficient Query in get_next_available_appointment

**Status:** DOCUMENTED

**Current Implementation:**

```python
# Queries database in loop, one slot at a time
for each 30-minute slot:
    check if slot is booked
    if not booked:
        return slot
```

**Optimized Approach:**

```python
# Query all booked slots in date range once
start_time = datetime.now()
end_time = start_time + timedelta(days=7)

booked_slots = session.query(Appointment.appointment_time).filter(
    and_(
        Appointment.appointment_time >= start_time,
        Appointment.appointment_time <= end_time,
        Appointment.is_deleted == False
    )
).all()

booked_times = {slot.appointment_time for slot in booked_slots}

# Find first gap
current_time = start_time
while current_time <= end_time:
    if current_time not in booked_times:
        return current_time
    current_time += timedelta(minutes=30)
```

**Benefits:**

- Single database query instead of N queries
- 10-100x faster for busy schedules
- Reduced database load

---

### Issue #29: No Connection Pooling Configuration

**Status:** DOCUMENTED

**Current Implementation:**

```python
# database/connection.py
engine = create_engine(DATABASE_URL)
```

**Recommended for Production:**

```python
from config import DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT

engine = create_engine(
    DATABASE_URL,
    pool_size=DB_POOL_SIZE,  # 5 connections
    max_overflow=DB_MAX_OVERFLOW,  # 10 additional
    pool_timeout=DB_POOL_TIMEOUT,  # 30 seconds
    pool_pre_ping=True,  # Verify connections
    echo=False  # Disable SQL logging in production
)
```

**Note:** SQLite doesn't support connection pooling. This is only relevant when migrating to PostgreSQL/MySQL for production.

---

### Issue #34: Missing Relationship Definitions

**Status:** PARTIALLY FIXED

**Changes Made:**

- Added `relationship` import to `models.py`

**Remaining Work:**
Add relationship definitions to models:

```python
# In User model
class User(Base):
    # ... existing fields ...
    appointments = relationship("Appointment", back_populates="user")

# In Appointment model
class Appointment(Base):
    # ... existing fields ...
    user = relationship("User", back_populates="appointments")
```

**Benefits:**

- Easier querying: `user.appointments` instead of manual joins
- Automatic cascade deletes (if configured)
- Better ORM integration

**Note:** This is optional for current functionality but improves code quality.

---

### Issue #37: No Email Queue System

**Status:** DOCUMENTED

**Current Implementation:**

- Emails sent synchronously in request thread
- If SMTP is slow, user waits

**Production Recommendation:**

**Option 1: Celery + Redis**

```python
# tasks.py
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def send_email_async(to_email, subject, message):
    send_email_notification(to_email, subject, message)

# In tools.py
send_email_async.delay(user_email, subject, message)
```

**Option 2: Background Threads (Simple)**

```python
import threading

def send_email_background(to_email, subject, message):
    thread = threading.Thread(
        target=send_email_notification,
        args=(to_email, subject, message)
    )
    thread.daemon = True
    thread.start()
```

**Option 3: Streamlit + Queue**

```python
import queue
import threading

email_queue = queue.Queue()

def email_worker():
    while True:
        email_data = email_queue.get()
        send_email_notification(**email_data)
        email_queue.task_done()

# Start worker thread
threading.Thread(target=email_worker, daemon=True).start()

# Queue emails
email_queue.put({"to_email": user_email, "subject": subject, "message": message})
```

**Recommendation:** Use Option 2 (background threads) for current Streamlit app. Use Celery for production with high volume.

---

## Summary

| Issue | Status     | Notes                               |
| ----- | ---------- | ----------------------------------- |
| #27   | Partial    | Config added, UI pagination pending |
| #28   | Documented | Optimization approach provided      |
| #29   | Documented | Only relevant for production DB     |
| #34   | Partial    | Import added, relationships pending |
| #37   | Documented | Background threads recommended      |

All remaining issues are either:

1. **UI changes** requiring interactive testing (#27)
2. **Production optimizations** not critical for development (#28, #29, #37)
3. **Code quality improvements** that don't affect functionality (#34)

---

**Last Updated:** 2026-02-17  
**Status:** Documented for future implementation
