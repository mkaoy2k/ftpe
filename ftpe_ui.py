"""
Family Tree Platform - 管理介面模組

此模組提供完整的家族樹平台管理介面，包括：
- 使用者認證與授權（登入、重設密碼）
- 家族成員管理（新增、編輯、刪除成員）
- 家族管理（家族設定、權限管理）
- 資料匯入/匯出功能
- 平台管理功能（僅限平台管理員）

主要功能：
- 提供三種使用者角色：家族成員、家族管理員、平台管理員
- 支援多國語言介面
- 響應式設計，適應不同裝置
- 資料匯出為多種格式（CSV, Excel, JSON）

注意：
- 此模組使用 Streamlit 框架建置網頁介面
- 依賴多個自訂模組處理資料庫操作、電子郵件發送等功能
"""
from dotenv import load_dotenv
import os
import sqlite3
import db_utils as dbm
import email_utils as eu
import auth_utils as au
import funcUtils as fu
import pandas as pd

# Import database operations
from ops_dbMgmt import init_db_management, init_admin_features, get_table_structure, drop_table
import context_utils as cu

# Load environment variables
load_dotenv()

import streamlit as st

# Set initial page config (will be updated after login)
st.set_page_config(
    page_title= os.getenv("APP_NAME", "") + " " + os.getenv("RELEASE", ""),
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None  # This will be updated after login
)

def show_reset_password_page():
    """Display the password reset page"""
    st.header("Reset Password")
    
    # Initialize reset state if not exists
    if 'reset_token' not in st.session_state:
        st.session_state.reset_token = None
    if 'reset_email' not in st.session_state:
        st.session_state.reset_email = None
    if 'reset_error' not in st.session_state:
        st.session_state.reset_error = None
    if 'reset_success' not in st.session_state:
        st.session_state.reset_success = None
    
    # Always check for token in URL parameters first
    token_param = st.query_params.get("token")
    if token_param:
        if isinstance(token_param, list):
            token_param = token_param[0] if token_param else None
        if token_param and token_param != st.session_state.get('reset_token'):
            st.session_state.reset_token = token_param
            st.session_state.reset_email = None  # Reset email to force reload from token
            st.rerun()  # Rerun to ensure state is updated
    
    # Center the form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Show back to login link
        if st.button("← Back to Login"):
            st.session_state.show_forgot_password = False
            st.rerun()
            
        st.markdown("<h2 style='text-align: center;'>Reset Password</h2>", unsafe_allow_html=True)
        
        # Display error message if exists
        if st.session_state.reset_error:
            st.error(st.session_state.reset_error)
            
        # Display success message if exists
        if st.session_state.reset_success:
            st.success(st.session_state.reset_success)
        
        # Get token from URL parameters first (if coming from email link)
        token_param = st.query_params.get('token')
        if token_param and isinstance(token_param, list):
            token_param = token_param[0]  # Get the first token if multiple
            
        # Use token from URL if available, otherwise use session token
        token = token_param or st.session_state.get('reset_token')
        
        if token:
            # Store token in session state
            st.session_state.reset_token = token
            
            # Get email from session state or database
            email = st.session_state.get('reset_email')
            
            # If email is not in session state, try to get it from the token
            if not email:
                try:
                    try:
                        with dbm.get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT email FROM password_reset_tokens 
                                WHERE token = ? AND expires_at > datetime('now')
                            """, (token,))
                            result = cursor.fetchone()
                            
                            if result:
                                email = result[0]
                                st.session_state.reset_email = email
                            else:
                                error_msg = "Invalid or expired token. Please request a new password reset."
                                st.error(error_msg)
                                return
                    except Exception as e:
                        error_msg = f"Error verifying token: {str(e)}"
                        st.error(error_msg)
                        return
                except Exception as e:
                    st.error(f"Error verifying token: {str(e)}")
                    return
            
            # Show the reset password form with the email
            st.write("### Reset Your Password")
            st.write(f"Please enter a new password for: **{email}**")
            
            with st.form("reset_password_form"):
                new_password = st.text_input("New Password", 
                                          type="password", 
                                          key="new_password",
                                          help="Enter a strong password with at least 8 characters")
                
                confirm_password = st.text_input("Confirm New Password", 
                                              type="password", 
                                              key="confirm_password",
                                              help="Please re-enter your new password")
                
                reset_button = st.form_submit_button("Reset Password", 
                                                  type="primary",
                                                  use_container_width=True)
                
                if reset_button:
                    # Validate input
                    if not new_password or not confirm_password:
                        st.session_state.reset_error = "Please enter and confirm your new password"
                        st.rerun()
                    elif new_password != confirm_password:
                        st.session_state.reset_error = "Passwords do not match"
                        st.rerun()
                    elif len(new_password) < 8:
                        st.session_state.reset_error = "Password must be at least 8 characters long"
                        st.rerun()
                    else:
                        try:
                            with dbm.get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT email FROM password_reset_tokens 
                                    WHERE token = ? AND email = ? AND expires_at > datetime('now')
                                """, (token, email))
                                if cursor.fetchone():
                                    # Update password
                                    password_hash, salt = au.hash_password(new_password)
                                    cursor.execute("""
                                        UPDATE users 
                                        SET password_hash = ?, salt = ?, updated_at = datetime('now')
                                        WHERE email = ?
                                    """, (password_hash, salt, email))
                                    
                                    # Delete used token
                                    cursor.execute("""
                                        DELETE FROM password_reset_tokens 
                                        WHERE token = ?
                                    """, (token,))
                                    
                                    conn.commit()
                                    
                                    # Clear form state
                                    st.session_state.pop('new_password', None)
                                    st.session_state.pop('confirm_password', None)
                                    
                                    # Set success message and reset state
                                    st.session_state.reset_success = "Password has been reset successfully. You can now login with your new password."
                                    st.session_state.reset_error = None
                                    st.session_state.reset_token = None
                                    st.session_state.reset_email = None
                                    st.rerun()
                                else:
                                    st.session_state.reset_error = "Invalid or expired token. Please request a new password reset."
                                    st.session_state.reset_token = None
                                    st.session_state.reset_email = None
                                    st.rerun()
                        except Exception as e:
                            st.session_state.reset_error = f"Error resetting password: {str(e)}"
                            st.rerun()
        # If no token, show email input form
        else:
            with st.form("request_reset_form"):
                email = st.text_input("Email Address", key="reset_email")
                request_button = st.form_submit_button("Send Reset Link")
                
                if request_button:
                    st.session_state.reset_error = None
                    
                    if not email:
                        st.session_state.reset_error = "Please enter your email address"
                    else:
                        try:
                            with dbm.get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT id FROM users 
                                    WHERE email = ?
                                """, (email,))
                                if cursor.fetchone():
                                    token = eu.generate_verification_token()
                                    
                                    # Get expiration hours from environment variable
                                    expires_hours = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRY_HOURS', '24'))
                                    
                                    cursor.execute("""
                                        INSERT OR REPLACE INTO password_reset_tokens 
                                        (email, token, created_at, expires_at)
                                        VALUES (?, ?, datetime('now'), datetime('now', ? || ' hours'))
                                    """, (email, token, str(expires_hours)))
                                    
                                    reset_link = f"{os.getenv('FT_SVR', 'http://localhost:8501')}/?token={token}"
                                    
                                    subject = "Password Reset Request"
                                    text = f"""
                                    Hello,
                                    
                                    You have requested to reset your password. Please click the link below to reset your password:
                                    
                                    {reset_link}
                                    
                                    This link will expire in {expires_hours} hours.
                                    
                                    If you did not request this, please ignore this email.
                                    
                                    Regards,
                                    {os.getenv('APP_NAME', 'FamilyTreePE')} Team
                                    """
                                    
                                    html = f"""
                                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                                        <h2>Password Reset Request</h2>
                                        <p>Hello,</p>
                                        <p>You have requested to reset your password. Please click the button below to reset your password:</p>
                                        <p style="text-align: center; margin: 30px 0;">
                                            <a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                                Reset Password
                                            </a>
                                        </p>
                                        <p>Or copy and paste this link into your browser:</p>
                                        <p><code>{reset_link}</code></p>
                                        <p>This link will expire in {expires_hours} hours.</p>
                                        <p>If you did not request this, please ignore this email.</p>
                                        <p>Regards,<br>{os.getenv('APP_NAME', 'FamilyTreePE')} Team</p>
                                    </div>
                                    """
                                    
                                    publisher = eu.EmailPublisher(
                                        email_sender=eu.Config.MAIL_USERNAME,
                                        email_password=eu.Config.MAIL_PASSWORD
                                    )
                                    
                                    if publisher.publish_email(subject, text, html, [email]):
                                        st.session_state.reset_success = f"Password reset link has been sent to {email}. Please check your email."
                                        st.session_state.reset_error = None
                                    else:
                                        st.session_state.reset_error = "Failed to send password reset email. Please try again later."
                                else:
                                    st.session_state.reset_success = "If your email exists in our system, you will receive a password reset link."
                                    st.session_state.reset_error = None
                                    
                                conn.commit()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error processing your request: {str(e)}")

def show_login_page():
    """Display the login page"""
    global UI_TEXTS
    
    # Clear any existing content
    st.empty()
    
    # Initialize forgot password message in session state if not exists
    if 'show_forgot_password' not in st.session_state:
        st.session_state.show_forgot_password = False
    
    # Check for password reset token in URL
    token = st.query_params.get("token")
    if token and not st.session_state.show_forgot_password:
        if isinstance(token, list):
            token = token[0] if token else None
        if token:
            st.session_state.show_forgot_password = True
            st.session_state.reset_token = token
            st.rerun()
    
    # Forgot Password page
    if st.session_state.show_forgot_password:
        show_reset_password_page()
        return  # Important: Don't show login form if showing reset password
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown(f"<h2 style='text-align: center;'>{UI_TEXTS['user']} {UI_TEXTS['login']}</h2>", unsafe_allow_html=True)
            
            # Login form
            email = st.text_input(f"{UI_TEXTS['email']}", key="login_email")
            password = st.text_input(f"{UI_TEXTS['password']}", type="password", key="login_password")
                
            # Login and Forgot Password buttons
            col1, col2  = st.columns([2,1])
            with col1:
                login_clicked = st.button(f"{UI_TEXTS['login']}", type="primary")
            with col2:
                forgot_clicked = st.button(f"{UI_TEXTS['forgot']} {UI_TEXTS['password']}?",
                                           type="secondary",
                                           icon="🔑")
            
            # Handle Forgot Password button click
            if forgot_clicked:
                st.session_state.show_forgot_password = True
                st.rerun()
            
            # Handle login
            if login_clicked:                    
                # Validate input
                if not email or not password:
                    st.error(f"{fu.get_function_name()} {UI_TEXTS['field']} {UI_TEXTS['required']}")
                else:
                    # Verify credentials
                    if au.verify_padmin(email, password):
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        st.session_state.user_state = dbm.User_State['p_admin']
                        st.session_state.login_error = None
                        st.rerun()
                    elif au.verify_fadmin(email, password):
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        st.session_state.user_state = dbm.User_State['f_admin']
                        st.session_state.login_error = None
                        st.rerun()
                    elif au.verify_fmember(email, password):
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        st.session_state.user_state = dbm.User_State['f_member']
                        st.session_state.login_error = None
                        st.rerun()
                    else:
                        st.error(f"{fu.get_function_name()} {UI_TEXTS['email']} or {UI_TEXTS['password']} {UI_TEXTS['not_found']}")

def show_fmember_sidebar():
    """Display the family member sidebar with 
    personal navigation options"""
    global UI_TEXTS
    
    # Hide the default navigation for members
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.sidebar.title(f"{UI_TEXTS['family']} {UI_TEXTS['member']} {UI_TEXTS['sidebar']}")
        
        # Display current login email
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
            cu.update_context({
                'email_user': st.session_state.user_email
            })
        
        # Display navigation options
        st.sidebar.subheader(f"{UI_TEXTS['navigation']}")
        st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
        st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
        st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="🌲")
        st.page_link("pages/6_show_3G.py", label="Show 3 Generations", icon="👥")
        st.page_link("pages/7_show_related.py", label="Show Related", icon="👨‍👩‍👧‍👦")
        
        # Display Logout button at the bottom
        if st.button(f"{UI_TEXTS['logout']}", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    
def show_fadmin_sidebar():
    """Display the family admin sidebar with 
    limited family admin navigation options"""
    global UI_TEXTS
    
    # Hide the default navigation for members
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.sidebar.title(f"{UI_TEXTS['family']} {UI_TEXTS['admin']} {UI_TEXTS['sidebar']}")
        if st.session_state.user_state != dbm.User_State['p_admin']:
            # Hide the default navigation for non-padmin users
            st.markdown("""
            <style>
                [data-testid="stSidebarNav"] {
                    display: none !important;
                }
            </style>""", unsafe_allow_html=True)
        
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
            cu.update_context({
                'email_user': st.session_state.user_email
            })
        
        # Page Navigation Links
        st.subheader(f"{UI_TEXTS['navigation']}")
        st.page_link("ftpe_ui.py", label="Home", icon="🏠")
        st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
        st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
        st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="📊")
        st.page_link("pages/6_show_3G.py", label="Show 3 Generations", icon="👥")            
        st.page_link("pages/7_show_related.py", label="Show Related", icon="👨‍👩‍👧‍👦")
        st.page_link("pages/8_caseMgmt.py", label="Case Management", icon="📋")
        st.page_link("pages/9_birthday.py", label="Birthday", icon="🎂")
        st.page_link("pages/2_famMgmt.py", label="Family Management", icon="🌲")
 
        # Logout button at the bottom
        if st.button(f"{UI_TEXTS['logout']}", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
        
        # Display current family admin users
        st.sidebar.subheader(f"{UI_TEXTS['current']} {UI_TEXTS['family']} {UI_TEXTS['admin']} {UI_TEXTS['user']}")
        try:
            admins = dbm.get_users(role=dbm.User_State['f_admin'])
            if admins:
                admin_list = [
                        {
                            "Email": admin['email'],
                            "Created": fu.format_timestamp(admin['created_at']),
                            "Last Updated": fu.format_timestamp(admin['updated_at'])
                        }
                        for admin in admins
                ]
                # Convert to DataFrame to handle index properly
                df = pd.DataFrame(admin_list)
                st.dataframe(
                    df,
                    use_container_width=False,
                    hide_index=True  # Explicitly hide the index
                )  
            else:
                st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['admin']} {UI_TEXTS['user']} {UI_TEXTS['not_found']}")
            
        except sqlite3.Error as e:
            st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['db_error']}: {e}") 
        st.divider()

        # Display current family subscribers
        st.sidebar.subheader(f"{UI_TEXTS['current']} {UI_TEXTS['family']} {UI_TEXTS['subscriber']}")
        try:
            subscribers = dbm.get_subscribers()
            if subscribers:
                sub_list = [
                        {
                            "Email": sub['email'],
                            "Created": fu.format_timestamp(sub['created_at']),
                            "Last Updated": fu.format_timestamp(sub['updated_at'])
                        }
                        for sub in subscribers
                ]
                 # Convert to DataFrame to handle index properly
                df = pd.DataFrame(sub_list)
                st.dataframe(
                    df,
                    use_container_width=False,
                    hide_index=True  # Explicitly hide the index
                )
            else:
                st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['subscriber']} {UI_TEXTS['not_found']}")
                
        except sqlite3.Error as e:
            st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['db_error']}: {e}")
       
def show_padmin_sidebar():
    """Display the platform admin sidebar"""
    global UI_TEXTS
    
    with st.sidebar:
        st.sidebar.title("Platform Admin Sidebar")
        
        # Display current login email
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
            cu.update_context({
                'email_user': st.session_state.user_email
            })
        
        # Display current platform admin info
        st.sidebar.subheader(f"{UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['user']} {UI_TEXTS['management']}")
        with st.expander(f"{UI_TEXTS['create']} {UI_TEXTS['or']} {UI_TEXTS['update']} {UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['user']}", expanded=False):
            with st.form("admin_user_form"):
                st.subheader(f"{UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['user']}")
                email = st.text_input("Email", key="padmin_email", 
                                   help="Enter the email address for the admin user")
                new_password = st.text_input("Password", type="password", key="new_password",
                                          help="Enter a password (at least 8 characters)")
                confirm_password = st.text_input("Confirm Password", type="password", 
                                               key="confirm_password")
                
                if st.form_submit_button(f"{UI_TEXTS['save']} {UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['user']}"):
                    if not email or not eu.validate_email(email):
                        st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['email']} {UI_TEXTS['not_found']}: {email}")
                    elif not new_password:
                        st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['password']} {UI_TEXTS['not_found']}")
                    elif new_password != confirm_password:
                        st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['password_error']}")
                    elif len(new_password) < 8:
                        st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['password']} {UI_TEXTS['at_least_eight_characters']}")
                    else:
                        user_id = au.create_user(
                            email, new_password, 
                            role=dbm.User_State['p_admin'])
                        if user_id:
                            st.success(f"✅ {UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['user']} {UI_TEXTS['created']} {UI_TEXTS['successfully']}")
                        else:
                            st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['user']} {UI_TEXTS['created']} {UI_TEXTS['failed']}")
    
        # Display Logout button at the bottom
        if st.sidebar.button(f"{UI_TEXTS['logout']}", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()

        # Display current platform admin users
        st.sidebar.subheader(f"{UI_TEXTS['current']} {UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['user']}")
        try:
            admins = dbm.get_users(role=dbm.User_State['p_admin'])
                
            if admins:
                admin_data = [
                    {
                        "Email": admin['email'],
                        "Created": fu.format_timestamp(admin['created_at']),
                        "Last Updated": fu.format_timestamp(admin['updated_at'])
                    }
                    for admin in admins
                ]
                
                # Convert to DataFrame to handle index properly
                df = pd.DataFrame(admin_data)
                st.dataframe(
                    df,
                    use_container_width=False,
                    hide_index=True  # Explicitly hide the index
                )
            else:
                st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['admin']} {UI_TEXTS['user']} {UI_TEXTS['not_found']}")
            
        except sqlite3.Error as e:
            st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['db_error']}: {e}")

def show_fmember_content():
    """Display the family member content area"""
    global UI_TEXTS
    
    st.header(f"{UI_TEXTS['family']} {UI_TEXTS['member']} {UI_TEXTS['home']}")
    
    show_front_end()
    
    # Search Family Members
    search_members_page()
    
    # Reset Password Management
    reset_password_page()
    
def reset_password_page():
    """
    Display the reset password page on which users can reset 
    their password.
    """
    global UI_TEXTS
    
    # Initialize form state if not exists
    if 'reset_form_submitted' not in st.session_state:
        st.session_state.reset_form_submitted = False
    
    with st.form("reset_password_form"):
        st.subheader(f"{UI_TEXTS['reset']} {UI_TEXTS['password']} {UI_TEXTS['page']}")
        email = st.session_state.user_email
        st.markdown(f"{UI_TEXTS['email']}: {email}")
        new_password = st.text_input(
            f"{UI_TEXTS['password']}", 
            type="password", 
            key="reset_new_password",
            help=f"{UI_TEXTS['enter']} {UI_TEXTS['password']}")
        
        confirm_password = st.text_input(
            f"{UI_TEXTS['confirm']} {UI_TEXTS['password']}", 
            type="password", 
            key="confirm_new_password",
            help=f"{UI_TEXTS['confirm']} {UI_TEXTS['password']}")
        
        submit_button = st.form_submit_button(f"{UI_TEXTS['submit']}", type="primary")
        
        if submit_button:
            st.session_state.reset_form_submitted = True
    
    # Handle form submission outside the form context
    if st.session_state.reset_form_submitted:
        error_messages = []
        
        # Validate inputs
        if not new_password:
            error_messages.append(f"❌ {UI_TEXTS['password']} {UI_TEXTS['field']} {UI_TEXTS['required']}")
        if len(new_password) < 8:
            error_messages.append(f"❌ {UI_TEXTS['password']} {UI_TEXTS['field']} {UI_TEXTS['at_least_eight_characters']}")
        if new_password != confirm_password:
            error_messages.append(f"❌ {UI_TEXTS['password_error']}")
        
        # If no validation errors, try to reset password
        if not error_messages:
            try:
                # Use reset_password function instead of create_user
                success = au.reset_password(email, new_password)
                if success:
                    st.success(f"✅ {UI_TEXTS['password']} {UI_TEXTS['reset']} {UI_TEXTS['successfully']}")
                    st.info(f"ℹ️ {UI_TEXTS['login_with_new_password']}")
                    st.session_state.reset_form_submitted = False
                    
                    # Clear the form
                    st.session_state.new_password = ""
                    st.session_state.confirm_new_password = ""
                    
                    # Add a button to go to login page
                    if st.button(f"← {UI_TEXTS['back_to_login']}"):
                        st.session_state.show_reset_password = False
                        st.rerun()
                else:
                    error_messages.append(f"❌ {UI_TEXTS['password_reset_failed']}")
            except Exception as e:
                error_messages.append(f"❌ {UI_TEXTS['error_occurred']}: {str(e)}")
        
        # Display all error messages if any
        for error in error_messages:
            st.error(error)

def search_members_page() -> None:
    """
    Display the member search page with filters and results.
    """
    global UI_TEXTS
    
    # Initialize session state and UI_TEXTS
    if 'app_context' not in st.session_state:
        cu.init_session_state()

    # Get UI_TEXTS with a fallback to English if needed
    try:
        UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', 'US')]
    except (KeyError, AttributeError):
        # Fallback to English if there's any issue
        UI_TEXTS = st.session_state.ui_context['US']
    
    # Initialize session state for search results
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    # Search form
    with st.form("search_form"):
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['member']}")
        
        # Create three rows of search fields
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row3_col1, row3_col2, row3_col3 = st.columns(3)
        
        with row2_col1:
            name = st.text_input(UI_TEXTS['name'], "")
        with row1_col2:
            born = st.text_input(
                UI_TEXTS['born'],
                "",
                placeholder="in YYYY-MM-DD format"
            )
        with row1_col3:
            gen_order = st.number_input(
                UI_TEXTS['gen_order'],
                min_value=0,
                step=1,
                value=0
            )
        with row3_col1:
            alias = st.text_input(UI_TEXTS['alias'], "")
        with row2_col2:
            died = st.text_input(
                UI_TEXTS['died'],
                "",
                placeholder="in YYYY-MM-DD format"
            )
        with row2_col3:
            family_id = st.number_input(
                f"{UI_TEXTS['family']} {UI_TEXTS['id']}", 
                        min_value=0, step=1, value=0)
            
        # Third row of search filters
        with row1_col1:
            member_id = st.number_input(
                f"{UI_TEXTS['member']} {UI_TEXTS['id']}",
                min_value=0,
                step=1,
                value=0
            )
        with row3_col2:
            email = st.text_input(UI_TEXTS['email'], "")
        with row3_col3:
            sex = st.selectbox(
                UI_TEXTS['sex'],
                ["", "Male", "Female", "Other"]
            )

        # Search button
        submitted = st.form_submit_button(f"{UI_TEXTS['search']}", type="primary")
        
        if submitted:
            with st.spinner(f"{UI_TEXTS['search']} {UI_TEXTS['in_progress']} ..."):
                # Execute search
                results = dbm.search_members(
                    name=name if name else "",
                    alias=alias if alias else "",
                    family_id=family_id if family_id > 0 else 0,
                    gen_order=gen_order if gen_order > 0 else 0,
                    born=born if born else "",
                    died=died if died else "",
                    id=member_id if member_id > 0 else 0,
                    email=email if email else "",
                    sex={"Male": "M", "Female": "F", "Other": "O"}.get(sex, "") if sex else ""
                )
                if results: 
                    st.session_state.search_results = results
                else:
                    st.session_state.search_results = []
    
            # Display search results
            if st.session_state.search_results:
                st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
                
                # Prepare data for display
                df = pd.DataFrame(st.session_state.search_results)
        
                # Define all fields from dbm.db_tables['members'] table
                all_fields = dbm.get_table_columns(dbm.db_tables['members'])
        
                # Ensure all columns exist in the dataframe
                for field in all_fields:
                    if field not in df.columns:
                        df[field] = None
                        
                # Convert date columns to string to avoid serialization issues
                date_columns = ['born', 'died', 'created_at', 'updated_at']
                for col in date_columns:
                    if col in df.columns and not df[col].empty:
                        df[col] = df[col].astype(str)
        
                # Display data table with all fields
                st.dataframe(
                    df[all_fields],
                    column_config={
                        'id': 'ID',
                        'name': 'Name',
                        'family_id': 'Family ID',
                        'alias': 'Alias',
                        'email': 'Email',
                        'url': 'Website',
                        'born': 'Birth Date',
                        'died': 'Death Date',
                        'sex': 'Gender',
                        'gen_order': 'Generation',
                        'dad_id': 'Father ID',
                        'mom_id': 'Mother ID',
                        'created_at': 'Created At',
                        'updated_at': 'Updated At'
                    },
                    hide_index=True,
                    use_container_width=True,
                    column_order=all_fields
                )
        
                # Show result count
                st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['count']}: {len(df)} records")
                st.success(f"✅ {UI_TEXTS['successful']} {UI_TEXTS['search']}")
            elif submitted:
                # No results message
                st.warning(f"⚠️ {UI_TEXTS['no_results_found_for']} {UI_TEXTS['member']}")

def show_fadmin_content() -> None:
    """Display the family admin content area"""
    global UI_TEXTS
    
    st.header(f"{UI_TEXTS['family']} {UI_TEXTS['admin']} {UI_TEXTS['home']}")
    
    show_front_end()
    
    # Search Family Members
    search_members_page()
    
    # Family Subscription Management
    with st.container(border=True):
        st.subheader(f"{UI_TEXTS['family']} {UI_TEXTS['subscription']} {UI_TEXTS['management']}")

        col21, col22 = st.columns(2)
        with col22:
            new_password = st.text_input(UI_TEXTS['password'], type="password", key="new_password",
                    help="Enter a password (at least 8 characters)")
            confirm_password = st.text_input(UI_TEXTS['password_confirmed'], type="password", 
                    key="confirm_password")

        with col21:
            # Common form fields
            email = st.text_input(UI_TEXTS['email'], key="family_admin_email", 
                help="Enter the email address for the family admin/subscriber")
            # Language selection
            lang_list = fu.get_languages()
            if not lang_list:
                lang_list = ["US", "繁中"]
            
            current_lang = st.session_state.app_context.get('language')
            lang_index = 0
            if current_lang and current_lang in lang_list:
                lang_index = lang_list.index(current_lang)
            
            l10n = st.selectbox(
                f"{UI_TEXTS['select']} {UI_TEXTS['subscription']} {UI_TEXTS['language']}",
                lang_list,
                index=lang_index,
                key="l10n_select"
            )
    
        # Create two separate forms for the buttons
        col1, col2 = st.columns(2)
    
        # Display success message if it exists in session state
        if 'success_message' in st.session_state and st.session_state.success_message:
            st.success(st.session_state.success_message)
            # Clear the message after displaying it
            del st.session_state.success_message
            
        # Form for Family Admin
        with col2:
            with st.form("admin_form"):
                st.markdown(f"### {UI_TEXTS['create']} {UI_TEXTS['family']} {UI_TEXTS['admin']}")
                # Create the CSS and HTML with the admin question
                admin_question = UI_TEXTS['only_family_admin?']
                css_html = f"""
                <style>
                @keyframes blink {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.2; }}
                    100% {{ opacity: 1; }}
                }}
                .blink {{
                    animation: blink 1.5s infinite;
                }}
                </style>
                <h4 class="blink">{admin_question}</h4>
                """
                st.markdown(css_html, unsafe_allow_html=True)
                st.markdown(f"{UI_TEXTS['create_backup_family_admin']}")
                
                # Store form state
                form_submitted = st.form_submit_button(
                    f"{UI_TEXTS['create']} {UI_TEXTS['family']} {UI_TEXTS['admin']}",
                    type="primary")
                
                if form_submitted:
                    error_messages = []
                    
                    if not email or not eu.validate_email(email):
                        error_messages.append("Please enter a valid email address")
                    if not new_password:
                        error_messages.append("Please enter a password")
                    elif new_password != confirm_password:
                        error_messages.append("Passwords do not match")
                    elif len(new_password) < 8:
                        error_messages.append("Password must be at least 8 characters long")
                    
                    if error_messages:
                        for msg in error_messages:
                            st.error(f"❌ {msg}")
                    else:
                        results = dbm.search_members(email=email)
                        if len(results) > 1:
                            st.error(f"❌ Multiple users found with the same email {email}")
                        elif len(results) == 1:
                            user_id = au.create_user(
                                email, new_password, 
                                role=dbm.User_State['f_admin'])
                            if user_id:
                                # Add as a subscriber by default for family admin
                                success, message = dbm.add_subscriber(email, "By Family Admin", lang=l10n)
                                if success:
                                    # Save success message in session state before rerun
                                    st.session_state.success_message = f"✅ {UI_TEXTS['family']} {UI_TEXTS['admin']} & {UI_TEXTS['subscriber']} {UI_TEXTS['created']} {UI_TEXTS['successfully']}"
                                    # Clear form on success by rerunning with cleared state
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                            else:
                                st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['family']} {UI_TEXTS['admin']} {UI_TEXTS['created']} {UI_TEXTS['failed']}")
                        else:
                            st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['first']}, {UI_TEXTS['To become a family admin, you must join this family as member first']}")
    
        # Form for Family Subscriber
        with col1:
            with st.form("subscriber_form"):
                st.markdown(f"### {UI_TEXTS['family']} {UI_TEXTS['member']} {UI_TEXTS['subscription']}")
                action = st.radio(f"{UI_TEXTS['select']}", 
                        [UI_TEXTS['subscribe'], UI_TEXTS['unsubscribe']])
                
                # Store form state
                form_submitted = st.form_submit_button(f"{UI_TEXTS['submit']}", type="primary")
                
                if form_submitted:
                    error_messages = []
                    
                    if not email or not eu.validate_email(email):
                        error_messages.append("Please enter a valid email address")
                    
                    if action == UI_TEXTS['unsubscribe']:
                        # Remove subscriber if Unsubscribe is selected
                        if dbm.remove_subscriber(email):
                            st.success(f"✅ Family member {email} unsubscribed successfully")
                        else:
                            st.error(f"❌ Failed to unsubscribe {email}")
                    else:
                        if not new_password:
                            error_messages.append("Please enter a password")
                        elif new_password != confirm_password:
                            error_messages.append("Passwords do not match")
                        elif len(new_password) < 8:
                            error_messages.append("Password must be at least 8 characters long")
                        
                        if error_messages:
                            for msg in error_messages:
                                st.error(f"❌ {msg}")
                        else:
                            results = dbm.search_members(email=email)
                            if len(results) > 1:
                                st.error(f"❌ Multiple users found with the same email {email}")
                            elif len(results) == 1:
                                user_id = au.create_user(
                                    email, new_password, 
                                    role=dbm.User_State['f_member'])
                                if user_id and action == UI_TEXTS['subscribe']:
                                    success, message = dbm.add_subscriber(email, "By Family Admin", lang=l10n)
                                    if success:
                                        st.success(f"✅ Family member {email} subscribed successfully")
                                        # Clear form on success
                                        st.session_state.new_password = ""
                                        st.session_state.confirm_password = ""
                                        st.session_state.family_admin_email = ""
                                    else:
                                        st.error(f"❌ {message}")
                                else:
                                    st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['family']} {UI_TEXTS['member']} {UI_TEXTS['created']} {UI_TEXTS['failed']}")
                            else:
                                st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['first']}, {UI_TEXTS['join_family_as']} {UI_TEXTS['subscriber']}")
    
    available_tables =  [os.getenv("TBL_MEMBERS", "members"),
                 os.getenv("TBL_RELATIONS", "relations"),
                 os.getenv("TBL_MIRRORS", "mirrors")]
    show_back_end(available_tables)
    
    # Reset Password Management
    reset_password_page()
    
# Helper function to get full file path with extension
def get_file_path():
    """Generate full file path with correct extension 
    based on selected file type.
    
    Returns:
        str: Full file path with extension or None if 
        file name or file type is not configured 
    """
    context = st.session_state.get('app_context', {})
    if not context.get('fss', {}).get('file_name') or not context.get('fss', {}).get('file_type'):
        return None 
        
    extension = context.get('fss', {}).get('file_type', '').lower()
    dir_path = context.get('fss', {}).get('dir_path', '')
    file_name = context.get('fss', {}).get('file_name', '')
    
    return f"{os.path.join(dir_path, file_name)}.{extension}"
    
# Helper function to handle export operations
def handle_export(export_func, file_path, table):
    """Handle export operations with proper error handling and user feedback."""
    try:        
        st.info(f"Exporting '{table}' table to {file_path}")
                
        results = export_func(file_path, table)
        if results.get('success'):
            st.success(f"✅ Successfully exported '{table}' table to {file_path}")
        else:
            st.error(f"❌ Failed to export '{table}' table: {results.get('message')}")
                
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
    
# Helper function to handle import operations
def handle_import(import_func, file_path, table):
    """Handle import operations with proper error handling and user feedback."""
    try:
        if not file_path or not os.path.exists(file_path):
            st.warning(f"⚠️ File not found: {file_path or 'No file specified'}")
            return
            
        st.info(f"Importing {file_path} to '{table}' table")       
        result = import_func(file_path, table)
        st.info(f"Import {file_path} to {table} completed. ")
        if result['success']:
            st.success(f"✅ Successfully imported {result['imported']} records to '{table}' table")
        else:
            for error in result.get('errors', []):
                st.error(f"❌ {error}")
            st.info(f"Imported: {result['imported']}, Skipped: {result['skipped']}")
            
    except Exception as e:
        st.error(f"❌ An error occurred during import: {str(e)}")

def show_front_end():
    global UI_TEXTS
    # Create form with a unique key
    with st.form(key="front_end_form"):
        st.subheader(f"{UI_TEXTS['front_end']} {UI_TEXTS['settings']}")
        col1, col2 = st.columns(2)
        
        with col1:
            # Get current settings
            current_timezone = st.session_state.app_context.get('timezone', 'UTC')
            
            # Timezone selection
            timezone = st.selectbox(
                f"{UI_TEXTS['timezone']}",
                ["UTC", "America/Los_Angeles", "Asia/Taipei"],
                index=["UTC", "America/Los_Angeles", "Asia/Taipei"].index(current_timezone) 
                if current_timezone in ["UTC", "America/Los_Angeles", "Asia/Taipei"] else 0,
                key="timezone_select"
            )
            
            # Default email
            default_email = st.text_input(
                f"{UI_TEXTS['family']} {UI_TEXTS['admin']} {UI_TEXTS['email']}", 
                value=st.session_state.app_context.get('email_user', ''),
                key="default_email"
            )
            email_subscription = st.checkbox(
                f"{UI_TEXTS['email']} {UI_TEXTS['subscription']}", 
                value=st.session_state.app_context.get('email_subscription', True),
                key="email_subscription"
            )
            submitted = st.form_submit_button(f"{UI_TEXTS['save']} {UI_TEXTS['settings']}", type="primary")
            
        with col2:
            # Language selection
            lang_list = fu.get_languages()
            if not lang_list:
                lang_list = ["US", "繁中"]
                
            current_lang = st.session_state.app_context.get('language')
            lang_index = 0
            if current_lang and current_lang in lang_list:
                lang_index = lang_list.index(current_lang)
                
            language = st.selectbox(
                f"{UI_TEXTS['language']}",
                lang_list,
                index=lang_index,
                key="language_select"
            )
            
            admin_email = st.text_input(
                f"{UI_TEXTS['platform']} {UI_TEXTS['admin']} {UI_TEXTS['email']}", 
                value=st.session_state.app_context.get('email_admin', ''),
                key="platform_admin_email"
            )
        
            dark_mode = st.checkbox(
                f"{UI_TEXTS['dark_mode']}", 
                value=st.session_state.app_context.get('dark_mode', False),
                key="dark_mode"
            )
        
            refresh = st.form_submit_button(f"{UI_TEXTS['refresh']}", type="secondary")
        
    # Handle form submission
    if refresh:
        st.rerun()
    if submitted:
        # Update settings in session state
        st.session_state.app_context.update({
            'timezone': timezone,
            'email_user': default_email,
            'language': language,
            'email_admin': admin_email,
            'email_subscription': email_subscription,
            'dark_mode': dark_mode
        })
        
        # Update context
        cu.update_context(st.session_state.app_context)
        UI_TEXTS = st.session_state.ui_context[language]

        st.success(f"{UI_TEXTS['settings']} {UI_TEXTS['updated']} {UI_TEXTS['successfully']}")

def show_back_end(available_tables):
    global UI_TEXTS
    
    # Ensure fss settings exist in the context
    if 'fss' not in st.session_state.app_context:
        st.session_state.app_context['fss'] = {}
    
    # Set default values if they don't exist
    if 'dir_path' not in st.session_state.app_context['fss']:
        st.session_state.app_context['fss']['dir_path'] = './data'
    if 'file_name' not in st.session_state.app_context['fss']:
        st.session_state.app_context['fss']['file_name'] = 'backup'
    if 'file_type' not in st.session_state.app_context['fss']:
        st.session_state.app_context['fss']['file_type'] = 'CSV'
    if 'db_tables' not in st.session_state.app_context['fss']:
        st.session_state.app_context['fss']['db_tables'] = available_tables
    if 'db_table' not in st.session_state.app_context['fss']:
        # Default to 'members' table if available, otherwise use the first table in the list
        st.session_state.app_context['fss']['db_table'] = available_tables[0] if available_tables else ''
    
    # File system settings section
    with st.form("Back-end Form"):
        st.subheader(f"{UI_TEXTS['back_end']} {UI_TEXTS['DB']} {UI_TEXTS['backup']} {UI_TEXTS['settings']}")

        # Directory path input
        dir_path = st.text_input(
            f"{UI_TEXTS['dir_path']}",
            value=st.session_state.app_context['fss'].get('dir_path', ''),
            help="Enter the directory path where files will be saved/loaded"
        )
   
        col11, col12, col13 = st.columns([2, 1, 1])
        with col11:
            # DB table selection
            current_table = st.session_state.app_context.get('fss', {}).get('db_table', '')
            
            # Find the index of current_table, default to 0 if not found
            try:
                table_index = available_tables.index(current_table)
            except ValueError:
                table_index = 0
            
            db_table = st.selectbox(
                f"{UI_TEXTS['DB']} {UI_TEXTS['table']}",
                available_tables,
                index=table_index,
                help="Select the database table for import/export"
            )
        with col12:
            # File name input
            file_name = st.text_input(
                f"{UI_TEXTS['file_name']}",
                value=st.session_state.app_context['fss'].get('file_name', ''),
                help="Enter the base file name (without extension)"
            )
        with col13:
            # File type selection
            file_type = st.selectbox(
                f"{UI_TEXTS['file_type']}",
                ["JSON", "CSV"],
                index=0 if not st.session_state.app_context.get('fss', {}).get('file_type') else 
                    ["JSON", "CSV"].index(st.session_state.app_context.get('fss', {}).get('file_type', 'JSON')),
                help="Select the file format for import/export"
            )
        choice = st.radio(f"{UI_TEXTS['select']}:", ["Export", "Import"])
        if st.form_submit_button(f"{UI_TEXTS['submit']}", type="primary"):
            cu.update_context({
                'fss': {
                    'dir_path': dir_path,
                    'file_name': file_name,
                    'file_type': file_type,
                    'db_tables': available_tables,
                    'db_table': db_table
                }
            })
            file_path = get_file_path()
            if file_path and choice == "Export":
                handle_export(dbm.export_to_file, file_path, db_table)
            elif file_path and choice == "Import":
                handle_import(dbm.import_from_file, file_path, db_table)
   
def show_padmin_content():
    """Display the main content area for platform admin"""
    global UI_TEXTS
    st.title(f"{UI_TEXTS['platform_admin']} {UI_TEXTS['home']}")
    
    # Show database tables
    st.header(f"{UI_TEXTS['DB']} {UI_TEXTS['table']} {UI_TEXTS['management']}")
    available_tables = init_db_management()
    
    if not available_tables:
        st.info("No tables found in the database.")
        return
    # Display tables in a select box
    selected_table = st.selectbox(f"{UI_TEXTS['select']} {UI_TEXTS['table']}", available_tables)
    
    if selected_table:
        # Show table structure
        st.subheader(f"{UI_TEXTS['table']} {UI_TEXTS['structure']}: {selected_table}")
        columns = get_table_structure(selected_table)
        cu.update_context({
            'fss': {
                'db_tables': available_tables,
                'db_table': selected_table
            }
        })
       
        if columns:
            # Display columns in a table
            column_data = []
            for col in columns:
                col_info = {
                    "Column Name": col[1],
                    "Data Type": col[2],
                    "Allow NULL": "No" if col[3] else "Yes",
                    "Default": col[4] or "None",
                    "Primary Key": "Yes" if col[5] else "No"
                }
                column_data.append(col_info)
            st.table(column_data)
            
            # Drop table button
            with st.expander(UI_TEXTS['danger_zone'], expanded=False):
                st.warning("⚠️ This action cannot be undone!")
                if st.button(f"Drop Table '{selected_table}'", type="primary"):
                    if drop_table(selected_table):
                        st.success(f"Dropped table '{selected_table}'")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to drop table '{selected_table}'")
            
            # Add column form
            with st.expander(UI_TEXTS['add'] + " " + UI_TEXTS['column'], expanded=False):
                with st.form("add_column_form"):
                    new_col_name = st.text_input("Column Name")
                    col_type = st.selectbox(
                        "Data Type",
                        ["INTEGER", "TEXT", "REAL", "BLOB", "NUMERIC"]
                    )
                    is_nullable = st.checkbox("Allow NULL", value=True)
                    default_value = st.text_input("Default Value", "")
                    
                    if st.form_submit_button("Add Column"):
                        if new_col_name:
                            try:
                                # Build the ALTER TABLE statement
                                stmt = f"ALTER TABLE {selected_table} ADD COLUMN {new_col_name} {col_type}"
                                if not is_nullable:
                                    stmt += " NOT NULL"
                                if default_value:
                                    stmt += f" DEFAULT '{default_value}'"
                                
                                with dbm.get_db_connection() as conn:
                                    conn.execute(stmt)
                                    conn.commit()
                                st.success(f"Added column '{new_col_name}' to table '{selected_table}'")
                                st.rerun()
                            except sqlite3.Error as e:
                                st.error(f"❌ Error adding column: {e}")
                        else:
                            st.error("❌ Please enter a column name")
            
            # Drop column form
            with st.expander(UI_TEXTS['remove'] + " " + UI_TEXTS['column'], expanded=False):
                if len(columns) > 1:  # Don't allow dropping the last column
                    with st.form("remove_column_form"):
                        col_to_remove = st.selectbox(
                            UI_TEXTS['select'] + " " + UI_TEXTS['column'] + " to remove",
                            [col[1] for col in columns if col[1] != "id"]  # Don't allow dropping id column
                        )
                        
                        if st.form_submit_button("Remove Column"):
                            if remove_column_if_exists(selected_table, col_to_remove):
                                st.success(f"Removed column '{col_to_remove}' from table '{selected_table}'")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to remove column '{col_to_remove}'")
                else:
                    st.warning("⚠️ Cannot remove the last column from a table")
        show_back_end(available_tables)
    
    # Reset Password Management
    reset_password_page()
    
# Main application
def main():
    """Main application entry point"""
    global UI_TEXTS

    # Initialize admin features (adds necessary columns to user table)
    if not init_admin_features():
        st.error(f"❌ {UI_TEXTS['admin_init_error']}")
        st.stop()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_page()
    else:
        # Initialize or get context
        if 'app_context' not in st.session_state:
            st.session_state.app_context = cu.init_context()
        
        # Retrieve the member_id and family_id via login-email and
        # update the application context
        email_user = st.session_state.get('user_email', '')
        member = dbm.get_member_by_email(email_user)
        if not member:
            member = {
            'id': 0,
            'family_id': 0
        }
        cu.update_context({
            'member_id': member['id'],
            'family_id': member['family_id']
        })    

        if st.session_state.user_state == dbm.User_State['p_admin']:
            show_padmin_sidebar()
            show_padmin_content()
        elif st.session_state.user_state == dbm.User_State['f_admin']:
            show_fadmin_sidebar()
            show_fadmin_content()
        elif st.session_state.user_state == dbm.User_State['f_member']:
            show_fmember_sidebar()
            show_fmember_content()

# Initialize session state
cu.init_session_state()
UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', "US")]
    
if __name__ == "__main__":
    main()