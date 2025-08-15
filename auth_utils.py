"""
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


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
                    st.warning(f"⚠️ Error updating login time: {update_error}")
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
                    st.warning(f"⚠️ Error updating login time: {update_error}")
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
                    st.warning(f"⚠️ Error updating login time: {update_error}")
                    # Continue even if update fails, as auth was successful
                return True
            
            return False
            
    except sqlite3.Error as e:
        st.error(f"Error verifying admin: {e}")
        return False

def create_password_reset_token(email: str, expires_hours: int = 24) -> str:
    """Create a password reset token for the given email
    
    Args:
        email: The email address to create a token for
        expires_hours: Number of hours until the token expires (default: 24)
        
    Returns:
        str: The generated token if successful, None otherwise
    """
    try:
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert the token into the database
            cursor.execute("""
                INSERT INTO password_reset_tokens (
                    email, 
                    token, 
                    expires_at
                ) VALUES (?, ?, datetime('now', ? || ' hours'))
            """, (email, token, str(expires_hours)))
            
            conn.commit()
            return token
            
    except Exception as e:
        st.error(f"Error creating password reset token: {e}")
        return None

def validate_password_reset_token(token: str) -> tuple:
    """Validate a password reset token
    
    Args:
        token: The token to validate
        
    Returns:
        tuple: (is_valid, email) where is_valid is a boolean indicating if the token is valid,
               and email is the associated email address if valid, None otherwise
    """
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if token exists and is not expired or used
            cursor.execute("""
                SELECT email 
                FROM password_reset_tokens 
                WHERE token = ? 
                AND used = 0 
                AND expires_at > datetime('now')
            """, (token,))
            
            result = cursor.fetchone()
            if result:
                return True, result[0]
            return False, None
            
    except Exception as e:
        st.error(f"Error validating password reset token: {e}")
        return False, None

def reset_password(email: str, new_password: str) -> bool:
    """Reset a user's password
    
    Args:
        email: The email address of the user
        new_password: The new password to set
        
    Returns:
        bool: True if the password was successfully reset, False otherwise
    """
    try:
        # Hash the new password
        password_hash, salt = hash_password(new_password)
        
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Update the user's password
            cursor.execute(f"""
                UPDATE {dbm.db_tables['users']}
                SET password_hash = ?,
                    salt = ?,
                    updated_at = datetime('now')
                WHERE email = ?
            """, (password_hash, salt, email))
            
            # Mark all tokens for this email as used
            cursor.execute("""
                UPDATE password_reset_tokens
                SET used = 1
                WHERE email = ?
            """, (email,))
            
            conn.commit()
            return cursor.rowcount > 0
            
    except Exception as e:
        st.error(f"Error resetting password: {e}")
        return False


def create_user (email, 
    password, 
    role=None,
    l10n="US",
    is_active=None,
    family_id=0, 
    member_id=0):
    """Create a new user
    
    Args:
        email: The email address of the user
        password: The password of the user
        role: The role of the user, see dbm.User_State
        
    Returns:
        id: The id of the user if the user was created 
        when not existed or updated when existed
        successfully, None otherwise.
    
    Raises:
        ValueError: If the role is not valid
        
    Examples:
        >>> create_user("test@example.com", "password", 
            role=dbm.User_State['f_admin'],
            l10n="US",
            is_active=dbm.Subscriber_State['inactive'],
            family_id=0, 
            member_id=0)
        1
    """
    try:
        # check if role is valid
        if role is not None and role not in dbm.User_State.values():
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
                        l10n = ?,
                        family_id = ?,
                        member_id = ?,
                        WHERE id = ?
                """, 
                (password_hash, salt, 
                 role, is_active, 
                 l10n, family_id, 
                 member_id, user_id)
                )
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
                        l10n,
                        family_id,
                        member_id,
                        created_at
                    ) 
                    VALUES (?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, 
                    datetime('now')
                    )
                """, (email, password_hash, salt, 
                      role, is_active, l10n, 
                      family_id, member_id))
                conn.commit()
                user_id = cursor.lastrowid
                return user_id
    except sqlite3.Error as e:
        error_msg = str(e)
        log.error(error_msg)
        return None

