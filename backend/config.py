"""
Configuration settings for AI Receptionist application
Centralized configuration to avoid hardcoded values
"""

import os
from pathlib import Path

# Base directories
# FIX BUG-31: config.py is in the project root, so parent IS the project root
# parent.parent was incorrectly pointing one level above the project
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
IMAGES_DIR = STATIC_DIR / "images"  # FIXED Issue #23: Configurable image directory
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# File upload settings (FIXED Issue #24, #25)
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': b'\xff\xd8\xff',
    'image/png': b'\x89PNG\r\n\x1a\n',
    'image/gif': b'GIF89a',
}

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///receptionist_star.db")
# Using the single database for everything
STAR_DATABASE_URL = DATABASE_URL

# Connection pooling settings (FIXED Issue #29)
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Timezone settings (FIXED Issue #22)
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

# Pagination settings (FIXED Issue #27)
DEFAULT_PAGE_SIZE = int(os.getenv("PAGE_SIZE", "50"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))

# FIXED Issue #41: Named constants for magic numbers
# Appointment scheduling constants
APPOINTMENT_SLOT_DURATION_MINUTES = 30  # Duration of each appointment slot
AVAILABILITY_SEARCH_DAYS = 7  # Days to search for available appointments
WORKING_HOURS_START = 9  # Start of working hours (9 AM)
WORKING_HOURS_END = 17  # End of working hours (5 PM)

# Password requirements
MIN_PASSWORD_LENGTH = 8
MIN_PASSWORD_LENGTH_LEGACY = 6  # Legacy minimum (deprecated)

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Application settings
APP_NAME = "AI Receptionist"
APP_VERSION = "1.0.0"
