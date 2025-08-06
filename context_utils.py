"""
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


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
SITE_TITLE = os.getenv("APP_NAME", "")
RELEASE = os.getenv("RELEASE", "")

# Language Settings
language_list = fu.get_languages()
LANGUAGES = language_list
LANGUAGE = os.getenv("L10N", "US")

# Email Settings
EMAIL_SUBSCRIPTION = True
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
    'file_name': os.getenv("FSS_FILE_NAME", "backup"),
    'file_type': os.getenv("FSS_FILE_TYPE", "CSV"),
    'db_table': os.getenv("TBL_MEMBERS", "members"),
    'db_tables': [os.getenv("TBL_MEMBERS", "members"),
                 os.getenv("TBL_RELATIONS", "relations"),
                 os.getenv("TBL_FAMILIES", "families"),
                 os.getenv("TBL_MIRRORS", "mirrors")]
}
# ===== End of Module Settings =====

def init_context() -> Dict[str, Any]:
    """
    Initialize and return a dictionary containing 
    application settings
    
    Returns:
        Dict[str, Any]: Dictionary containing settings
    """
    # Default settings
    default_settings = {
        'timezone': TIMEZONE,
        'site_title': SITE_TITLE,
        'language': LANGUAGE,
        'languages': LANGUAGES,
        'email_subscription': EMAIL_SUBSCRIPTION,
        'email_user': MAIL_USER,
        'email_pass': MAIL_PASS,
        'email_admin': MAIL_ADMIN,
        'ft_svr': FT_SVR,
        'fss': FILE_SYSTEM_SETTINGS,
        'dark_mode': DARK_MODE,
        'items_per_page': ITEMS_PER_PAGE,
        'password_reset_timeout': PASSWORD_RESET_TIMEOUT,
        'max_login_attempts': MAX_LOGIN_ATTEMPTS,
        'member_id': None,
        'family_id': None
    }
    
    return default_settings

# Function to update application context
def update_context(new_values: dict):
    if 'app_context' not in st.session_state:
        st.session_state.app_context = init_context()
    st.session_state.app_context.update(new_values)
    
def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'app_context' not in st.session_state:
        st.session_state.app_context = init_context()
    if 'ui_context' not in st.session_state:
        st.session_state.ui_context = fu.load_L10N()
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_state' not in st.session_state:
        st.session_state.user_state = dbm.User_State['f_member']
    if 'relation' not in st.session_state:
        st.session_state.relation = None
          
# Example usage
if __name__ == "__main__":
    init_session_state()
    update_context({'timezone': 'Asia/Taipei', 'language': '繁中'})
    print("Current context:", st.session_state.app_context)
    print("Current UI context:(US)", st.session_state.ui_context['US'])
    print("Current UI context:(繁中)", st.session_state.ui_context['繁中'])
