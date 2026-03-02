import sqlite3

try:
    conn = sqlite3.connect('p:/Project/MINI PROJECT/AI RESEPTIONIST/receptionist.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in db:")
    for table in tables:
        print(f"- {table[0]}")
    conn.close()
except Exception as e:
    print(f"Error checking database: {e}")
