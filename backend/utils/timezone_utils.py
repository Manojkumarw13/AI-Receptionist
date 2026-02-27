"""
Timezone utilities for AI Receptionist
Handles timezone-aware datetime operations
"""

import pytz
from datetime import datetime
from config import DEFAULT_TIMEZONE

# FIXED Issue #22: Timezone handling
def get_timezone():
    """Get the configured timezone."""
    return pytz.timezone(DEFAULT_TIMEZONE)

def now_with_timezone():
    """Get current time with timezone."""
    tz = get_timezone()
    return datetime.now(tz)

def make_aware(dt: datetime):
    """Convert naive datetime to timezone-aware."""
    if dt.tzinfo is None:
        tz = get_timezone()
        return tz.localize(dt)
    return dt

def to_local_time(dt: datetime):
    """Convert datetime to local timezone."""
    tz = get_timezone()
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(tz)
