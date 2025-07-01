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

def verify_member(email, password):
    """Verify member credentials and membership status
    
    Args:
        email: The email address of the member
        password: The password of the member
        
    Returns:
        bool: True if the credentials are valid and user is a member, False otherwise
    """
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, password_hash, salt 
                FROM {dbm.db_tables['users']} 
                WHERE email = ? 
                AND is_admin = {dbm.User_State['member']} 
            """, (email,))
            
            result = cursor.fetchone()
            if result is None:
                return False
                
            user_id, stored_hash, salt = result
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
                    st.warning(f"Error updating login time: {update_error}")
                    # Continue even if update fails, as auth was successful
                return True
            
            return False
            
    except sqlite3.Error as e:
        st.error(f"Error verifying member: {e}")
        return False


def verify_admin(email, password):
    """Verify admin credentials
    
    Args:
        email: The email address of the admin
        password: The password of the admin
        
    Returns:
        bool: True if the credentials are valid, False otherwise
    """
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, password_hash, salt  
                FROM {dbm.db_tables['users']} 
                WHERE email = ? 
                AND is_admin = {dbm.User_State['admin']} 
            """, (email,))
            
            result = cursor.fetchone()
            if result is None:
                return False
                
            user_id, stored_hash, salt = result
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
                    st.warning(f"Error updating login time: {update_error}")
                    # Continue even if update fails, as auth was successful
                return True
            
            return False
            
    except sqlite3.Error as e:
        st.error(f"Error verifying admin: {e}")
        return False

def create_admin_user(email, password):
    """Create a new admin user
    
    Args:
        email: The email address of the admin
        password: The password of the admin
        
    Returns:
        bool: True if the admin user was created successfully, False otherwise
    """
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
                        is_admin = {dbm.User_State['admin']}, 
                        is_active = {dbm.Subscriber_State['active']},
                        updated_at = strftime('%%Y-%%m-%%d %%H:%%M:%%f', 'now', 'localtime')
                    WHERE id = ?
                """, (password_hash, salt, user_id))
                conn.commit()
                return True, f"{user_id} updated to admin"
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
                    ) 
                    VALUES (?, ?, ?, 
                    {dbm.User_State['admin']}, 
                    {dbm.Subscriber_State['active']}, 
                    datetime('now'), 
                    datetime('now')
                    )
                """, (email, password_hash, salt))
                conn.commit()
                return True, f"Admin user created successfully"
    except sqlite3.Error as e:
        error_msg = str(e)
        log.error(error_msg)
        return False, error_msg

def create_member_user(email, password):
    """Create a new member user or update existing user to member status
    
    Args:
        email: The email address of the member
        password: The password for the member account
        
    Returns:
        tuple: (success: bool, message: str) - Success status and message
    """
    try:
        # Check if user already exists
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, is_admin FROM {dbm.db_tables['users']} 
                WHERE email = ?
            """, (email,))
            user = cursor.fetchone()
            
            if user:
                user_id = user[0]
                # Update existing user to member
                password_hash, salt = hash_password(password)
                cursor.execute(f"""
                    UPDATE {dbm.db_tables['users']} 
                    SET password_hash = ?, 
                        salt = ?,
                        is_admin = {dbm.User_State['member']}, 
                        is_active = {dbm.Subscriber_State['active']},
                        updated_at = strftime('%%Y-%%m-%%d %%H:%%M:%%f', 'now', 'localtime')
                    WHERE id = ?
                """, (password_hash, salt, user_id))
                conn.commit()
                return True, f"{user_id} updated to member"
            else:
                # Create new member user
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
                    ) 
                    VALUES (?, ?, ?, 
                    {dbm.User_State['member']}, 
                    {dbm.Subscriber_State['active']}, 
                    datetime('now'), 
                    datetime('now')
                    )
                """, (email, password_hash, salt))
                conn.commit()
                return True, f"Member user created successfully"
    except sqlite3.Error as e:
        error_msg = str(e)
        log.error(error_msg)
        return False, error_msg
