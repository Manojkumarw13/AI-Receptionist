"""
Migration script to add role-based access control fields to User model
Adds: role, name, is_active, last_login fields
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_session, init_db
from database.models import User
from sqlalchemy import text

def migrate_user_roles():
    """Add RBAC fields to existing users"""
    print("Starting User RBAC migration...")
    
    # Initialize database (creates tables if they don't exist)
    init_db()
    
    session = get_session()
    
    try:
        # Check if columns exist
        result = session.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        # Add columns if they don't exist
        if 'role' not in columns:
            print("Adding 'role' column...")
            session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
        
        if 'name' not in columns:
            print("Adding 'name' column...")
            session.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(255)"))
        
        if 'is_active' not in columns:
            print("Adding 'is_active' column...")
            session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"))
        
        if 'last_login' not in columns:
            print("Adding 'last_login' column...")
            session.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
        
        session.commit()
        
        # Set first user as admin if exists
        users = session.query(User).all()
        if users:
            first_user = users[0]
            if first_user.role == 'user':
                first_user.role = 'admin'
                if not first_user.name:
                    first_user.name = first_user.email.split('@')[0].title()
                session.commit()
                print(f"✅ Set {first_user.email} as admin")
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_user_roles()
