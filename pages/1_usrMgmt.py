"""
User Management Page

This page provides user management functionality including:
- Viewing table structures
- Adding/removing columns
- Managing tables
"""
import streamlit as st
import pandas as pd
import db_utils as dbm
from admin_ui import show_admin_sidebar, init_session_state
from context_utils import init_context, update_context
from db_utils import import_users_from_file, export_users_to_file
import sqlite3

def format_timestamps(df):
    """Convert UTC timestamps to Pacific Time (with DST) and format"""
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            # Parse as UTC and convert to Pacific Time (handles DST automatically)
            df[col] = pd.to_datetime(df[col], utc=True)
            df[col] = df[col].dt.tz_convert('America/Los_Angeles').dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def show_page():
    # Show admin sidebar
    show_admin_sidebar()
    context = st.session_state.get('app_context', init_context())
    
    st.title("User Table Management")
    try:
        # --- manage users --- from here
        st.markdown("---")
        st.subheader("Query Subscribers")
        df = pd.DataFrame()
        btn11, btn12, btn13, btn14 = st.columns([5,5,5,5])
        info1, info2, info3 = st.columns([18,1,1])
        with btn11:
            if st.button("Active"):
                users = dbm.get_subscribers(state="active")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} active subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No active subscribers found")    
        with btn12:
            if st.button("Inactive"):
                users = dbm.get_subscribers(state="inactive")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} inactive subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No inactive subscribers found")
        with btn13:
            if st.button("Pending"):
                users = dbm.get_subscribers(state="pending")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} pending subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No pending subscribers found") 
                        
        with btn14:
            if st.button("All"):
                users = dbm.get_subscribers('all')
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No subscribers found")
    
        # --- manage a specific user --- from here
        st.markdown("---")
        st.subheader("Manage User")
        # Create three columns for better layout
        col1, col2, col3 = st.columns([5,5,5])
        with col1:
            email = st.text_input(':blue[Email:]', 
                        value=context.get('default_email', 'mkaoy2k@gmail.com'))
            email = email.strip()
        with col2:
            lang_list = context.get('languages', ['US'])
            current_lang = context.get('language', 'US')
            # Ensure the current language is in the list to avoid ValueError
            default_index = 0
            if current_lang in lang_list:
                default_index = lang_list.index(current_lang)
            l10n = st.selectbox("Language:", 
                              lang_list,
                              index=default_index
                                )
        with col3:
            user_id = st.number_input("User ID:",
                                  min_value=1,
                                  max_value=100000,
                                  value=1)
        if st.button("Query"):
            user = dbm.get_subscriber(email)
            if user is not None:
                # Create a vertical display of user data
                st.write("### User Details")
                # Create three columns for better layout
                col1, col2, col3 = st.columns([5,5,5])
                
                # Display user data in a vertical format
                for i, (key, value) in enumerate(user.items()):
                    # Convert timestamp to local time if needed
                    if key in ['created_at', 'updated_at'] and value is not None:
                        value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
                    # Alternate between columns for better space usage
                    if i % 3 == 0:
                        col1.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    elif i % 3 == 1:
                        col2.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    else:
                        col3.write(f"**{key.replace('_', ' ').title()}:** {value}")
            else:            
                st.warning(f"Email '{email}' not found")
    
        btn21, btn22, btn23, btn24 = st.columns([5,5,5,5])
    
        with btn22:
            if st.button("Subscribe"):
                if dbm.add_subscriber(email, "token", lang=l10n):
                    update_context({'language': l10n})
                    st.info(f"Subscribed {email} successfully")
                else:
                    st.warning(f"Failed to subscribe {email}")
    
        with btn23:
            if st.button("Unsubscribe"):
                if dbm.remove_subscriber(email):
                    st.info(f"Unsubscribed {email} successfully")
                else:
                    st.warning(f"Failed to unsubscribe {email}")
    
        with btn21:
            if st.button("Delete by email"):
                if dbm.delete_subscriber(email):
                    st.info(f"Deleted {email} successfully")
                else:
                    st.warning(f"Failed to delete {email}")
        
        with btn24:
            if st.button("Delete by ID"):
                if dbm.delete_user(user_id):
                    st.info(f"Deleted {user_id} successfully")
                else:
                    st.warning(f"Failed to delete {user_id}")
        
        # --- import users --- from here
        st.markdown("---")
        st.subheader("Import Users From File to DB")
        col1, col2, col3 = st.columns([6,8,4])
        with col1:
            json_csv_file = st.text_input("File path to import from",
                          value="data/users.json",
                          placeholder="json or csv file format allowed")
        with col2:
            db_file = st.text_input("DB path to import to",
                          value="/Users/michaelkao/My_Projects/ftpe/data/family.db")
        with col3:
            table_name = st.text_input("Table name to import to",
                          value="users")
            
        if st.button("Import"):
            conn = sqlite3.connect(db_file)
            result = import_users_from_file(json_csv_file, conn, table_name)
            st.info(f"Imported: {result['imported']}, Skipped: {result['skipped']}")
            if result['errors']:
                st.error("\nErrors encountered:")
                for error in result['errors']:
                        st.error(f"- {error}")
        
        # --- export users --- from here
        st.markdown("---")
        st.subheader("Export Users From DB to File")
        col1, col2, col3 = st.columns([8,4,6])
        with col1:
            db_file = st.text_input("DB path to export from",
                          value="/Users/michaelkao/My_Projects/subs/data/users.db")
        with col2:
            table_name = st.text_input("Table name to export from",
                          value="user")
        with col3:
            json_csv_file = st.text_input("File path to export to",
                          value="data/users.json",
                          placeholder="json or csv file format allowed")
        
        if st.button("Export"):
                conn = sqlite3.connect(db_file)
                result = export_users_to_file(json_csv_file, conn, table_name)
                if result['success']:
                    st.info(result['message'])
                    st.info(result['file_path'])
                else:
                    st.error(result['message'])
    
    except Exception as err:
        st.error(f"An error occurred: {str(err)}")

# Initialize session state
init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
else:
    show_page()
