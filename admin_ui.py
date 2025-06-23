"""
Admin UI Module

This module provides the complete admin interface for the application.
"""
import streamlit as st

# 頁面配置必須是第一個 Streamlit 命令
st.set_page_config(
    page_title="Admin DBM",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

from difflib import context_diff
import sqlite3
import db_utils as dbm
import auth_utils

# Import database operations
from ops_dbMgmt import init_db_management, init_admin_features, get_table_structure, drop_table
from context_utils import init_context

def show_login_page():
    """Display the login page"""
    # Clear any existing content
    st.empty()
    
    # Set page title and header
    st.title("Database Management")
    st.markdown("---")
    
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
                        if auth_utils.verify_admin(email, password):
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.rerun()
                        else:
                            st.error("Invalid email or password")

def show_admin_sidebar():
    """Display the admin sidebar"""
    with st.sidebar:
        st.title("Admin Sidebar")
        
        # Show current user info
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
        
        # Sidebar - Admin User Management
        st.markdown("---")
        st.subheader("Admin User Management")
        with st.expander("Create/Update Admin User", expanded=False):
            with st.form("admin_user_form"):
                st.subheader("Admin User")
                email = st.text_input("Email", key="admin_email", 
                                   help="Enter the email address for the admin user")
                new_password = st.text_input("Password", type="password", key="new_password",
                                          help="Enter a password (at least 8 characters)")
                confirm_password = st.text_input("Confirm Password", type="password", 
                                               key="confirm_password")
                
                if st.form_submit_button("Save Admin User"):
                    if not email or "@" not in email:
                        st.error("Please enter a valid email address")
                    elif not new_password:
                        st.error("Please enter a password")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    else:
                        success, message = auth_utils.create_admin_user(email, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            
        # Display current admin users
        st.subheader("Current Admin Users")
        try:
            with dbm.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                        SELECT email, created_at, updated_at 
                        FROM users
                        WHERE is_admin = 1
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
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()

def show_main_content():
    """Display the main content area"""
    
    st.title("Admin DBM")
    st.markdown("---")
    
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

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None

def remove_column_if_exists(table_name, column_name):
    """Remove a column from a table if it exists"""
    try:
        with dbm.get_db_connection() as conn:
            # SQLite doesn't support DROP COLUMN directly, so we need to:
            # 1. Create a new table without the column
            # 2. Copy data from old table to new table
            # 3. Drop old table
            # 4. Rename new table to old table name
            
            # Get table info
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall() if col[1] != column_name]
            
            if not columns:
                return False  # Can't remove the last column
                
            # Create new table
            new_table = f"{table_name}_new"
            cursor.execute(f"CREATE TABLE {new_table} AS SELECT {', '.join(columns)} FROM {table_name} WHERE 1=0")
            
            # Copy data
            cursor.execute(f"INSERT INTO {new_table} SELECT {', '.join(columns)} FROM {table_name}")
            
            # Drop old table
            cursor.execute(f"DROP TABLE {table_name}")
            
            # Rename new table
            cursor.execute(f"ALTER TABLE {new_table} RENAME TO {table_name}")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        st.error(f"Error removing column: {e}")
        return False

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
        if not st.session_state.get('authenticated', False):
            show_login_page()
        else:
            # 初始化或獲取 context
            if 'app_context' not in st.session_state:
                st.session_state.app_context = init_context()
            show_admin_sidebar()
            # Main content
            show_main_content()

if __name__ == "__main__":
    main()