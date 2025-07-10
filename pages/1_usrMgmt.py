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
from ftpe_ui import show_admin_sidebar, show_member_sidebar
import context_utils as cu

def format_timestamps(df):
    """Convert UTC timestamps to Pacific Time (with DST) and format"""
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            # Parse as UTC and convert to Pacific Time (handles DST automatically)
            df[col] = pd.to_datetime(df[col], utc=True)
            df[col] = df[col].dt.tz_convert('America/Los_Angeles').dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def show_page():
    # Initialize logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Default context values
    default_context = {
        'languages': ['US'],
        'language': 'US',
        'mail_user': 'mkaoy2k@gmail.com'
    }
    
    try:
        logger.debug("Initializing show_page")
        
        # Initialize or get context from session state
        if 'app_context' not in st.session_state or not isinstance(st.session_state.app_context, dict):
            logger.debug("Initializing new app_context")
            context = default_context.copy()
            try:
                initialized_context = cu.init_context()
                if isinstance(initialized_context, dict):
                    context.update(initialized_context)
                st.session_state.app_context = context
            except Exception as init_error:
                logger.error(f"Error initializing context: {init_error}", exc_info=True)
                st.session_state.app_context = default_context
        
        # Get context from session state
        context = st.session_state.get('app_context', default_context)
        logger.debug(f"Context: {context}")
        
        # Ensure all required keys exist
        for key, default_value in default_context.items():
            if key not in context or context.get(key) is None:
                context[key] = default_value
        
        # Update session state with validated context
        st.session_state.app_context = context
        logger.debug(f"Final context: {context}")
        
        if st.session_state.user_state == dbm.User_State['admin']:
            # Show admin sidebar
            show_admin_sidebar()
        elif st.session_state.user_state == dbm.User_State['member']:
            # Show member sidebar
            show_member_sidebar()
        else:
            st.error("You do not have permission to access this page.")
            return
        
        st.title("User Management")
        
    except Exception as e:
        logger.error(f"Error initializing page: {str(e)}", exc_info=True)
        st.error(f"An error occurred while initializing the page: {str(e)}")
        return
    
    try:
        # --- manage users --- from here
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
        st.subheader("Manage User")
        # Create four columns for better layout
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            email_value = context.get('mail_user', 'mkaoy2k@gmail.com')
            logger.debug(f"Setting email input with value: {email_value}")
            email = st.text_input(':blue[Email:]', value=email_value)
            email = email.strip()
            
        with col2:
            lang_list = context.get('languages', ['US'])
            current_lang = context.get('language', 'US')
            logger.debug(f"Languages: {lang_list}, Current: {current_lang}")
            
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
        
        # Add a new column for creating member users
        st.subheader("Create New Member")
        with st.form("create_member_form"):
            new_email = st.text_input("New Email:", key="new_member_email")
            new_password = st.text_input("Password:", type="password", key="new_member_password")
            submitted = st.form_submit_button("Create Member")
            
            if submitted:
                if not new_email or not new_password:
                    st.warning("Please enter both email and password")
                else:
                    success, message = create_member_user(new_email, new_password)
                    if success:
                        st.success(message)
                        # The form will automatically clear on the next run
                    else:
                        st.error(f"Failed to create member: {message}")
        if st.button("Query User by Email"):
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
    
        btn21, btn22, btn23, btn24 = st.columns([1,1,1,1])
    
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
            if st.button("Delete User by Email"):
                if dbm.delete_subscriber(email):
                    st.info(f"Deleted {email} successfully")
                else:
                    st.warning(f"Failed to delete {email}")
        
        with btn24:
            if st.button("Delete User by ID"):
                if dbm.delete_user(user_id):
                    st.info(f"Deleted {user_id} successfully")
                else:
                    st.warning(f"Failed to delete {user_id}")
    except Exception as err:
        st.error(f"An error occurred: {str(err)}")
    
# Initialize session state
cu.init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    show_page()
