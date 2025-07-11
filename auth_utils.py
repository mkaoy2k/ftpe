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

def verify_fmember(email, password):
    """Verify family member credentials and membership status
    
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
                AND is_admin = {dbm.User_State['f_member']} 
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


def verify_padmin(email, password):
    """Verify platform admin credentials
    
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
                AND is_admin = {dbm.User_State['p_admin']} 
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

def verify_fadmin(email, password):
    """Verify family admin credentials
    
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
                AND is_admin = {dbm.User_State['f_admin']} 
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

def create_user(email, password, role, member_id=0):
    """Create a new user
    
    Args:
        email: The email address of the user
        password: The password of the user
        role: The role of the user, see dbm.User_State
        
    Returns:
        id: The id of the user if the user was created successfully, 
        None otherwise
    """
    try:
        # check if role is valid
        if role not in dbm.User_State.values():
            return None
        
        # Check if user already exists
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id 
                FROM {dbm.db_tables['users']} 
                WHERE email = ?
            """, (email,))
            
            existing_user = cursor.fetchone()
            if role == dbm.User_State['p_admin']:
                sub_state = dbm.Subscriber_State['active']
            elif role == dbm.User_State['f_admin']:
                sub_state = dbm.Subscriber_State['active']
            elif role == dbm.User_State['f_member']:
                sub_state = dbm.Subscriber_State['inactive']
            else:
                return None
            if existing_user:
                # Update existing user
                user_id = existing_user[0]
                password_hash, salt = hash_password(password)
                cursor.execute(f"""
                    UPDATE {dbm.db_tables['users']} 
                    SET password_hash = ?, 
                        salt = ?, 
                        is_admin = ?, 
                        is_active = ?,
                        member_id = ?,
                        updated_at = strftime('%%Y-%%m-%%d %%H:%%M:%%f', 'now', 'localtime')
                    WHERE id = ?
                """, (password_hash, salt, role, sub_state, member_id, user_id))
                conn.commit()
                return user_id
            else:
                # Create new user
                password_hash, salt = hash_password(password)
                cursor.execute(f"""
                    INSERT INTO {dbm.db_tables['users']} (
                        email, 
                        password_hash, 
                        salt, 
                        is_admin, 
                        is_active,
                        member_id,
                        created_at,
                        updated_at
                    ) 
                    VALUES (?, ?, ?, 
                    ?, 
                    ?, 
                    ?, 
                    datetime('now'), 
                    datetime('now')
                    )
                """, (email, password_hash, salt, 
                      role, sub_state, member_id))
                conn.commit()
                user_id = cursor.lastrowid
                return user_id
    except sqlite3.Error as e:
        error_msg = str(e)
        log.error(error_msg)
        return None

