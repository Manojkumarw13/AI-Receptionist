import sqlite3
import sys

try:
    conn = sqlite3.connect('p:/Project/MINI PROJECT/AI RESEPTIONIST/backend/receptionist.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, full_name, role FROM users WHERE email='test_script_user@example.com'")
    result = cursor.fetchone()
    if result:
        print(f"User found: {result}")
    else:
        print("User not found.")
    
    conn.close()
except Exception as e:
    print(f"Error checking database: {e}")
