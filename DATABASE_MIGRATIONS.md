# Database Migration Guide

## Overview

This project currently does not use a formal migration tool like Alembic. This document provides guidance for managing schema changes.

## FIXED Issue #31: Database Migration Strategy

### Current Approach (Development)

For development, the application uses SQLAlchemy's `create_all()` to create tables:

```python
from database.models import Base
from database.connection import engine

Base.metadata.create_all(engine)
```

### Recommended Production Approach

#### Option 1: Alembic (Recommended)

Install Alembic:

```bash
pip install alembic
```

Initialize Alembic:

```bash
alembic init alembic
```

Configure `alembic.ini`:

```ini
sqlalchemy.url = sqlite:///receptionist.db
```

Create migration:

```bash
alembic revision --autogenerate -m "Add status and soft delete fields"
```

Apply migration:

```bash
alembic upgrade head
```

#### Option 2: Manual SQL Migrations

For the recent schema changes (Issues #33, #35, #36), here are the SQL migrations:

**Migration: Add status, soft delete, and QR tracking**

```sql
-- Add status column
ALTER TABLE appointments ADD COLUMN status VARCHAR(50) DEFAULT 'Scheduled' NOT NULL;

-- Add soft delete flag
ALTER TABLE appointments ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL;

-- Add QR code path tracking
ALTER TABLE appointments ADD COLUMN qr_code_path VARCHAR(500);

-- Add updated_at timestamp
ALTER TABLE appointments ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Create index on status
CREATE INDEX idx_status ON appointments(status);
```

**Migration: Remove password from star schema**

```sql
-- This requires recreating the table (SQLite limitation)
-- 1. Create new table without password_hash
CREATE TABLE dim_user_new (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    age INTEGER,
    gender VARCHAR(20),
    blood_group VARCHAR(5),
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    emergency_contact VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

-- 2. Copy data (excluding password_hash)
INSERT INTO dim_user_new SELECT
    user_id, email, full_name, phone, age, gender, blood_group,
    address, city, state, pincode, emergency_contact, created_at, is_active
FROM dim_user;

-- 3. Drop old table
DROP TABLE dim_user;

-- 4. Rename new table
ALTER TABLE dim_user_new RENAME TO dim_user;

-- 5. Recreate indexes
CREATE UNIQUE INDEX idx_dim_user_email ON dim_user(email);
```

### Migration Checklist

Before applying migrations:

- [ ] Backup database
- [ ] Test migration on development database
- [ ] Review migration SQL
- [ ] Plan rollback strategy
- [ ] Schedule maintenance window (if needed)

After applying migrations:

- [ ] Verify schema changes
- [ ] Test application functionality
- [ ] Update documentation
- [ ] Monitor for errors

### Future Recommendations

1. **Use Alembic** for all future schema changes
2. **Version control** all migration files
3. **Test migrations** in staging before production
4. **Document** all schema changes
5. **Backup** before every migration

---

**Last Updated:** 2026-02-17  
**Status:** Migration strategy documented
