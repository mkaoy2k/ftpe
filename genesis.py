"""
Database Initialization Script

This script initializes the database with required tables and creates the first admin user.
"""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import db_utils as dbm

# Load environment variables
load_dotenv()

def create_admin_user():
    """Create the initial admin user"""
    email = os.getenv('DB_ADMIN')
    password = os.getenv('DB_ADMIN_PW')
    
    if not email or not password:
        print("❌ Error: DB_ADMIN and DB_ADMIN_PW must be set in .env file")
        return False
    
    try:
        # Import auth_utils here to avoid circular imports
        import auth_utils as auth
        
        # Create the admin user
        if auth.create_admin_user(email, password):
            print(f"✅ Successfully created admin user:")
            print(f"   Email: {email}")
            print(f"   Password: {'*' * len(password)}")
            return True
        else:
            print("❌ Failed to create admin user.")
            return False
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database initialization...")
    
    # Initialize database
    dbm.init_db()
    
    # Create admin user
    print("\n👤 Creating admin user...")
    if not create_admin_user():
        exit(1)
    
    print("\n✨ Database setup completed successfully!")
