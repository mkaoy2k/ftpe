"""
Context Utilities

This module provides utility functions for managing application context and settings.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv
import streamlit as st
import db_utils as dbm
import funcUtils as fu

# Load environment variables
load_dotenv()

# ===== Application Settings (Module Level) =====
# These settings can be imported by other modules using context_utils

# General Settings
TIMEZONE = os.getenv("TIMEZONE", "UTC")
ENABLE_MAINTENANCE = False
SITE_TITLE = os.getenv("APP_NAME", "")
RELEASE = os.getenv("RELEASE", "")

# Language Settings
language_list = fu.get_languages()
LANGUAGES = language_list
LANGUAGE = os.getenv("L10N", "US")

# Email Settings
EMAIL_NOTIFICATIONS = True
MAIL_USER = os.getenv("MAIL_USERNAME", "")
MAIL_PASS = os.getenv("MAIL_PASSWORD", "")
MAIL_ADMIN = os.getenv("DB_ADMIN", "")

# UI Settings
DARK_MODE = False
ITEMS_PER_PAGE = 20

# Security Settings
PASSWORD_RESET_TIMEOUT = 24  # hours
MAX_LOGIN_ATTEMPTS = 5

# Server Settings
FT_SVR=os.getenv("FT_SVR", "")

# File System Settings
FILE_SYSTEM_SETTINGS = {
    'dir_path': os.getenv("FSS_DIR_PATH", "./data"),
    'file_name': os.getenv("FSS_FILE_NAME", "users"),
    'file_type': os.getenv("FSS_FILE_TYPE", "CSV")
}
# ===== End of Module Settings =====

def init_context() -> Dict[str, Any]:
    """
    初始化並返回包含設定的全局字典
    
    Returns:
        Dict[str, Any]: 包含設定的字典
    """
    # Default settings
    default_settings = {
        'timezone': TIMEZONE,
        'enable_maintenance': ENABLE_MAINTENANCE,
        'site_title': SITE_TITLE,
        'language': LANGUAGE,
        'languages': LANGUAGES,
        'email_notifications': EMAIL_NOTIFICATIONS,
        'email_user': MAIL_USER,
        'email_pass': MAIL_PASS,
        'email_admin': MAIL_ADMIN,
        'ft_svr': FT_SVR,
        'fss': FILE_SYSTEM_SETTINGS,
        'dark_mode': DARK_MODE,
        'items_per_page': ITEMS_PER_PAGE,
        'password_reset_timeout': PASSWORD_RESET_TIMEOUT,
        'max_login_attempts': MAX_LOGIN_ATTEMPTS
    }
    
    return default_settings

# Function to update context
def update_context(new_values: dict):
    if 'app_context' not in st.session_state:
        st.session_state.app_context = init_context()
    st.session_state.app_context.update(new_values)
    
def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'app_context' not in st.session_state or st.session_state.app_context is None:
        st.session_state.app_context = init_context()
    if 'user_state' not in st.session_state:
        st.session_state.user_state = dbm.User_State['f_member']
          
# Example usage
if __name__ == "__main__":
    update_context({'timezone': 'Asia/Taipei'})
    print("Current context:", st.session_state.app_context)
