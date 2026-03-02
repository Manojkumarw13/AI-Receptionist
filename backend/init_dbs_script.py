import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_db, init_star_db
init_db()
init_star_db()
print("Databases initialized successfully.")
