"""
Admin UI Module

This module provides the complete admin interface for the application.
"""
from dotenv import load_dotenv
import os
import sqlite3
import db_utils as dbm
import email_utils as eu
import auth_utils as au
import funcUtils as fu
# Import database operations
from ops_dbMgmt import init_db_management, init_admin_features, get_table_structure, drop_table
from context_utils import init_session_state, init_context, update_context

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

def show_login_page():
    """Display the login page"""
    # Clear any existing content
    st.empty()
    
    # Set page title and header
    st.title(os.getenv("APP_NAME", "") + " " + os.getenv("RELEASE", ""))
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("<h2 style='text-align: center;'>Admin Login</h2>", unsafe_allow_html=True)
            
            # Login form
            with st.form("login_form"):
                email = st.text_input("Email Address", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submit_button = st.form_submit_button("Login")
                
                if submit_button:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        if au.verify_padmin(email, password):
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.user_state = dbm.User_State['p_admin']
                            st.rerun()
                        elif au.verify_fadmin(email, password):
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.user_state = dbm.User_State['f_admin']
                            st.rerun()
                        elif au.verify_fmember(email, password):
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.user_state = dbm.User_State['f_member']
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
def show_fmember_sidebar():
    """Display the family member sidebar with 
    personal navigation options"""
    
    # Hide the default navigation for members
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.sidebar.title("Family Member Sidebar")
        
        # Show current user info
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
        
        # Only show the following page options
        st.sidebar.subheader("Navigation")
        st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="🌲")
        
        # Add divider for spacing
        st.divider()
        
        # Logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    
def show_fadmin_sidebar():
    """Display the family admin sidebar with 
    limited family admin navigation options"""
    
    # Hide the default navigation for members
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.sidebar.title("Family Admin Sidebar")
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
        
        # Page Navigation Links
        st.subheader("Navigation")
        st.page_link("ftpe_ui.py", label="Home", icon="🏠")
        st.page_link("pages/2_famMgmt.py", label="Family Tree Management", icon="👤")
        st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
        st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
        st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="📊")
            
        st.divider()
        # Logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
       
def show_padmin_sidebar():
    """Display the platform admin sidebar"""
    with st.sidebar:
        st.sidebar.title("Platform Admin Sidebar")
        
        # Show current user info
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
        
        # Sidebar - Platform Admin User Management
        st.sidebar.subheader("PlatformAdmin User Management")
        with st.expander("Create/Update Platform Admin User", expanded=False):
            with st.form("admin_user_form"):
                st.subheader("Platform Admin User")
                email = st.text_input("Email", key="padmin_email", 
                                   help="Enter the email address for the admin user")
                new_password = st.text_input("Password", type="password", key="new_password",
                                          help="Enter a password (at least 8 characters)")
                confirm_password = st.text_input("Confirm Password", type="password", 
                                               key="confirm_password")
                
                if st.form_submit_button("Save Platform Admin User"):
                    if not email or not eu.validate_email(email):
                        st.error("Please enter a valid email address")
                    elif not new_password:
                        st.error("Please enter a password")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    else:
                        user_id = au.create_user(
                            email, new_password, 
                            role=dbm.User_State['p_admin'])
                        if user_id:
                            st.success("Platform Admin User created successfully")
                        else:
                            st.error("Failed to create Platform Admin User")
            
        # Display current platform admin users
        st.sidebar.subheader("Current Platform Admin Users")
        try:
            with dbm.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                        SELECT email, created_at, updated_at 
                        FROM {dbm.db_tables['users']}
                        WHERE is_admin = {dbm.User_State['p_admin']}
                        ORDER BY email
                    """)
                admins = cursor.fetchall()
                
                if admins:
                    admin_list = []
                    for email, created, updated in admins:
                        # Format timestamps for display
                        def format_timestamp(ts):
                            if not ts:
                                return "Never"
                            try:
                                # Try parsing as ISO format first
                                from datetime import datetime
                                if 'T' in str(ts):
                                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                else:
                                    # Try parsing as space-separated format
                                    dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                                return dt.strftime('%Y-%m-%d %H:%M:%S')
                            except (ValueError, TypeError):
                                return str(ts)
                        
                        admin_list.append({
                            "Email": email, 
                            "Created": format_timestamp(created), 
                            "Last Updated": format_timestamp(updated)
                        })
                    
                    st.table(admin_list)
                else:
                    st.info("No admin users found")
                
        except sqlite3.Error as e:
            st.error(f"Error fetching admin users: {e}")
    
        # Logout button at the bottom
        if st.sidebar.button("Logout", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()

def show_fmember_content():
    """Display the family member content area"""
    st.title("Family Member Home")
    context = st.session_state.get('app_context', init_context())
    
    # Reset Password Management
    st.subheader("Reset Password")
    with st.form("member_user_form"):
        new_password = st.text_input("New Password", type="password", key="new_password",
                    help="Enter a password (at least 8 characters)")
        confirm_password = st.text_input("Confirm New Password", type="password", 
                    key="confirm_password")
                
        if st.form_submit_button("Reset Password"):
            if not new_password:
                st.error("Please enter a password")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                email = st.session_state.user_email
                user_id = au.create_user(
                    email, new_password, 
                    role=dbm.User_State['f_member'])
                if user_id:
                    st.success("Family Member Password Reset successfully")
                else:
                    st.error("Failed to reset Family Member Password")

def show_fadmin_content():
    """Display the family admin content area"""
    st.title("Family Admin Home")
    context = st.session_state.get('app_context', init_context())

    show_front_end()
    
    # Family Admin User Management
    st.subheader("Family Admin User Management")
    with st.form("admin_user_form"):
        email = st.text_input("Email", key="family_admin_email", 
                    help="Enter the email address for the family admin user")
        new_password = st.text_input("Password", type="password", key="new_password",
                    help="Enter a password (at least 8 characters)")
        confirm_password = st.text_input("Confirm Password", type="password", 
                    key="confirm_password")
                
        if st.form_submit_button("Save Family Admin User"):
            if not email or not eu.validate_email(email):
                st.error("Please enter a valid email address")
            elif not new_password:
                st.error("Please enter a password")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                user_id = au.create_user(
                    email, new_password, 
                    role=dbm.User_State['f_admin'])
                if user_id:
                    st.success("Family Admin User created successfully")
                else:
                    st.error("Failed to create Family Admin User")
  
    show_back_end()
    
# Helper function to get full file path with extension
def get_file_path():
    """Generate full file path with correct extension 
    based on selected file type.
    """
    context = st.session_state.get('app_context', {})
    if not context.get('fss', {}).get('file_name') or not context.get('fss', {}).get('file_type'):
        return "No file path configured"
    extension = context.get('fss', {}).get('file_type', '').lower()
    dir_path = context.get('fss', {}).get('dir_path', '')
    file_name = context.get('fss', {}).get('file_name', '')
    return f"{os.path.join(dir_path, file_name)}.{extension}"
    
# Helper function to handle export operations
def handle_export(export_func, resource_name):
    """Handle export operations with proper error handling and user feedback."""
    try:
        file_path = get_file_path()
        if not file_path:
            st.error("Please provide both file name and directory path")
            return
                
        os.makedirs(context.get('fss', {}).get('dir_path'), exist_ok=True)
        format_type = context.get('fss', {}).get('file_type').lower()
            
        if export_func(file_path, format_type):
            st.success(f"Successfully exported {resource_name} to {file_path}")
        else:
            st.error(f"Failed to export {resource_name}. Please check the logs for details.")
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
# Helper function to handle import operations
def handle_import(import_func, resource_name):
    """Handle import operations with proper error handling and user feedback."""
    try:
        file_path = get_file_path()
        if not file_path or not os.path.exists(file_path):
            st.error(f"File not found: {file_path or 'No file specified'}")
            return
                
        format_type = context.get('fss', {}).get('file_type').lower()
        success, error, skipped = import_func(file_path, format_type)
            
        st.info(
            f"{resource_name} import completed. "
            f"Success: {success}, Errors: {error}, Skipped: {skipped}"
            )
            
    except Exception as e:
        st.error(f"An error occurred during import: {str(e)}")

def show_front_end():
    st.subheader("Front-end Settings")
   
    # Initialize context
    if 'app_context' not in st.session_state or st.session_state.app_context is None:
        st.session_state.app_context = init_context()
    
    # Create form with a unique key
    with st.form(key="front_end_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get current settings
            current_timezone = st.session_state.app_context.get('timezone', 'UTC')
            
            # Timezone selection
            timezone = st.selectbox(
                "Select Timezone",
                ["UTC", "America/Los_Angeles", "Asia/Taipei"],
                index=["UTC", "America/Los_Angeles", "Asia/Taipei"].index(current_timezone) 
                if current_timezone in ["UTC", "America/Los_Angeles", "Asia/Taipei"] else 0,
                key="timezone_select"
            )
            
            # Default email
            default_email = st.text_input(
                "Default Email", 
                value=st.session_state.app_context.get('email_user', ''),
                key="default_email"
            )
            
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
                "Select Language",
                lang_list,
                index=lang_index,
                key="language_select"
            )
            
            admin_email = st.text_input(
                "Admin Email", 
                value=st.session_state.app_context.get('email_admin', ''),
                key="frontend_admin_email"
            )
        
        # Checkbox options
        email_notifications = st.checkbox(
            "Enable Email Notifications", 
            value=st.session_state.app_context.get('email_notifications', True),
            key="email_notifications"
        )
        
        dark_mode = st.checkbox(
            "Enable Dark Mode", 
            value=st.session_state.app_context.get('dark_mode', False),
            key="dark_mode"
        )
        
        # Form submit button - must be the last element in the form
        submitted = st.form_submit_button("Save Settings")
        
    # Handle form submission
    if submitted:
        # Update settings in session state
        st.session_state.app_context.update({
            'timezone': timezone,
            'email_user': default_email,
            'language': language,
            'email_admin': admin_email,
            'email_notifications': email_notifications,
            'dark_mode': dark_mode
        })
        
        # Update context
        update_context(st.session_state.app_context)
        
        st.success("Settings updated successfully!")

def show_back_end():
    st.subheader("Back-end Settings")
    
    # File system settings section
    with st.form("Back-end Form"):
        # Directory path input
        dir_path = st.text_input(
            "Directory Path",
            value=st.session_state.app_context.get('fss', {}).get('dir_path', ''),
            help="Enter the directory path where files will be saved/loaded"
        )
        
        # File settings in columns for better layout
        col11, col12 = st.columns([3, 2])
        with col11:
            # File name input
            file_name = st.text_input(
                "File Name",
                value=st.session_state.app_context.get('fss', {}).get('file_name', ''),
                help="Enter the base file name (without extension)"
            )
        with col12:
            # File type selection
            file_type = st.selectbox(
                "File Type",
                ["JSON", "CSV"],
                index=0 if not st.session_state.app_context.get('fss', {}).get('file_type') else 
                    ["JSON", "CSV"].index(st.session_state.app_context.get('fss', {}).get('file_type', 'JSON')),
                help="Select the file format for import/export"
            )
        if st.form_submit_button("Save Back-end Settings"):
            update_context({
                'fss': {
                    'dir_path': dir_path,
                    'file_name': file_name,
                    'file_type': file_type
                }
            })
            file_path = get_file_path()
            st.success(f"{file_path} saved successfully!")
    
    col21, col22 = st.columns([1, 1])
    with col21:
        file_path = get_file_path()
        st.markdown("File Destination:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📤 Export Users", type="primary", help="Export user data to selected file format"):
            handle_export(dbm.export_users_to_file, 
                          dbm.db_tables['members'])
    with col22:
        file_path = get_file_path()
        st.markdown("File Source:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📥 Import Users", type="secondary", help="Import user data from selected file"):
            handle_import(dbm.import_users_from_file, 
                          dbm.db_tables['members'])
    
    col31, col32 = st.columns([1, 1])
    with col31:
        file_path = get_file_path()
        st.markdown("File Destination:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📤 Export Articles", type="primary", help="Export article data to selected file format"):
            handle_export(dbm.export_relations_to_file, 
                          dbm.db_tables['relations'])
    with col32:
        file_path = get_file_path()
        st.markdown("File Source:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📥 Import Articles", type="secondary", help="Import article data from selected file"):
            handle_import(dbm.import_articles_from_file, "Articles")
       
def show_padmin_content():
    """Display the main content area for platform admin"""
    
    st.title("Platform Admin Home")
   
    # Show database tables
    st.header("Database Tables")
    tables = init_db_management()
    
    if not tables:
        st.info("No tables found in the database.")
        return
    
    # Display tables in a select box
    selected_table = st.selectbox("Select a table", tables)
    
    if selected_table:
        # Show table structure
        st.subheader(f"Table Structure: {selected_table}")
        columns = get_table_structure(selected_table)
        
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
            
            # Add column form
            with st.expander("Add Column"):
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
                                st.error(f"Error adding column: {e}")
                        else:
                            st.error("Please enter a column name")
            
            # Drop column form
            with st.expander("Remove Column"):
                if len(columns) > 1:  # Don't allow dropping the last column
                    with st.form("remove_column_form"):
                        col_to_remove = st.selectbox(
                            "Select column to remove",
                            [col[1] for col in columns if col[1] != "id"]  # Don't allow dropping id column
                        )
                        
                        if st.form_submit_button("Remove Column"):
                            if remove_column_if_exists(selected_table, col_to_remove):
                                st.success(f"Removed column '{col_to_remove}' from table '{selected_table}'")
                                st.rerun()
                            else:
                                st.error(f"Failed to remove column '{col_to_remove}'")
                else:
                    st.warning("Cannot remove the last column from a table")
            
            # Drop table button
            with st.expander("Danger Zone", expanded=False):
                st.warning("This action cannot be undone!")
                if st.button(f"Drop Table '{selected_table}'", type="primary"):
                    if drop_table(selected_table):
                        st.success(f"Dropped table '{selected_table}'")
                        st.rerun()
                    else:
                        st.error(f"Failed to drop table '{selected_table}'")

# Main application
def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Initialize admin features (adds necessary columns to user table)
    if not init_admin_features():
        st.error("Failed to initialize admin features")
        st.stop()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_page()
    else:
        # Initialize or get context
        if 'app_context' not in st.session_state:
            st.session_state.app_context = init_context()
        if st.session_state.user_state == dbm.User_State['p_admin']:
            show_padmin_sidebar()
            show_padmin_content()
        elif st.session_state.user_state == dbm.User_State['f_admin']:
            show_fadmin_sidebar()
            show_fadmin_content()
        elif st.session_state.user_state == dbm.User_State['f_member']:
            show_fmember_sidebar()
            show_fmember_content()

if __name__ == "__main__":
    main()