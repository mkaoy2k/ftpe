"""
Authentication Utilities

This module handles authentication-related functions to avoid circular imports.
"""
import streamlit as st
import sqlite3
import hashlib
import secrets
import db_utils as dbm

def hash_password(password, salt=None):
    """Hash password with salt using PBKDF2"""
    if salt is None:
        salt = secrets.token_hex(16)  # Generate random salt
    
    # Use SHA-256 for password hashing
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),  # Convert password to bytes
        salt.encode('utf-8'),      # Use salt
        100000                     # Number of iterations
    ).hex()
    
    return password_hash, salt

def verify_admin(email, password):
    """Verify admin credentials"""
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, password_hash, salt, is_admin 
                FROM {dbm.db_tables['users']} 
                WHERE email = ? AND is_admin = 1
            """, (email,))
            
            result = cursor.fetchone()
            if result is None:
                return False
                
            user_id, stored_hash, salt, is_admin = result
            if not is_admin:
                return False
                
            input_hash, _ = hash_password(password, salt)
            
            if input_hash == stored_hash:
                # Update last login time with current timestamp
                try:
                    cursor.execute(f"""
                        UPDATE {dbm.db_tables['users']} 
                        SET updated_at = datetime('now')
                        WHERE id = ?
                    """, (user_id,))
                    conn.commit()
                except sqlite3.Error as update_error:
                    st.error(f"Error updating login time: {update_error}")
                    # Continue even if update fails, as auth was successful
                return True
            
            return False
            
    except sqlite3.Error as e:
        st.error(f"Error verifying admin: {e}")
        return False

def create_admin_user(email, password):
    """Create a new admin user"""
    try:
        # Check if user already exists
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM {dbm.db_tables['users']} WHERE email = ?", (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user to be admin
                user_id = existing_user[0]
                password_hash, salt = hash_password(password)
                cursor.execute(f"""
                    UPDATE {dbm.db_tables['users']} 
                    SET password_hash = ?, 
                        salt = ?, 
                        is_admin = 1, 
                        is_active = 1,
                        updated_at = strftime('%%Y-%%m-%%d %%H:%%M:%%f', 'now', 'localtime')
                    WHERE id = ?
                """, (password_hash, salt, user_id))
                conn.commit()
                return True, "Existing user updated to admin"
            else:
                # Create new admin user
                password_hash, salt = hash_password(password)
                cursor.execute(f"""
                    INSERT INTO {dbm.db_tables['users']} (
                        email, 
                        password_hash, 
                        salt, 
                        is_admin, 
                        is_active,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, 1, 1, 
                        datetime('now'), 
                        datetime('now')
                    )
                """, (email, password_hash, salt))
                conn.commit()
                return True, "Admin user created successfully"
                
    except sqlite3.Error as e:
        error_msg = str(e)
        st.error(f"Database error in create_admin_user: {error_msg}")
        return False, f"Error creating admin user: {error_msg}"
