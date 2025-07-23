"""
User Management Page

This page provides user management functionality including:
- Managing users
"""
import streamlit as st
import pandas as pd
import db_utils as dbm
from ftpe_ui import show_padmin_sidebar
import context_utils as cu
import auth_utils as au

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
    
    try:
        logger.debug("Initializing show_page")
        
        # Get context from session state
        context = st.session_state.get('app_context', cu.init_context())
        logger.debug(f"Context: {context}")
        
        if st.session_state.user_state == dbm.User_State['p_admin']:
            # Show admin sidebar
            show_padmin_sidebar()
        else:
            st.error("You do not have permission to access this page.")
            return
        
    except Exception as e:
        logger.error(f"❌ Error initializing page: {str(e)}", exc_info=True)
        st.error(f"❌ An error occurred while initializing the page: {str(e)}")
        return
    
    try:
        st.title("User Management")
        df = pd.DataFrame()
        
        # Subscriber Management
        st.subheader("Manage Subscriber")
        with st.container(border=True):
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

            # Create 2 columns for better layout
            col21, col22 = st.columns([2,1])
            with col21:
                email_value = st.session_state.get('user_email', '')
                logger.debug(f"Setting email input with value: {email_value}")
                email = st.text_input(':blue[Email:]', value=email_value, key="subscriber_email")
                email = email.strip()
                
            with col22:
                lang_list = context.get('languages', ['US'])
                current_lang = context.get('language', 'US')
                logger.debug(f"Languages: {lang_list}, Current: {current_lang}")
                
                # Ensure the current language is in the list to avoid ValueError
                default_index = 0
                if current_lang in lang_list:
                    default_index = lang_list.index(current_lang)
                l10n = st.selectbox("Language:", 
                                  lang_list,
                                  index=default_index,
                                  key="subscriber_language"
                                    )
            # Create the info31 column outside the query block to ensure it's always visible
            info31, info32 = st.columns([18,1])
            
            # Initialize user as None
            user = None
            
            if st.button("Query Subscriber by Email", type="primary", key="query_subscriber_btn"):
                user = dbm.get_subscriber(email)
                
            # Always show the subscriber details section, 
            # but only show content if user exists
            with info31:
                st.write("### Subscriber Details")
                
                if user is not None:
                    # Create three columns for better layout
                    col41, col42, col43 = st.columns([5,5,5])
                    
                    # Display user data in a vertical format
                    for i, (key, value) in enumerate(user.items()):
                        # Convert timestamp to local time if needed
                        if key in ['created_at', 'updated_at'] and value is not None:
                            value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Alternate between columns for better space usage
                        if i % 3 == 0:
                            col41.write(f"**{key.replace('_', ' ').title()}:** {value}")
                        elif i % 3 == 1:
                            col42.write(f"**{key.replace('_', ' ').title()}:** {value}")
                        else:
                            col43.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                btn41, btn42, btn43 = st.columns([1,1,1])
                with btn41:
                    if st.button("Subscribe", type="secondary", key="subscribe_btn"):
                        success, message = dbm.add_subscriber(email, "By Platform Admin", lang=l10n)
                        if success:
                            cu.update_context({'language': l10n})
                            st.success(f"✅ Subscribed {email} successfully")
                        else:
                            st.error(f"❌ {message}")
                with btn42:
                    if st.button("Unsubscribe", type="secondary", key="unsubscribe_btn"):
                        if dbm.remove_subscriber(email):
                            st.success(f"✅ Unsubscribed {email} successfully")
                        else:
                            st.error(f"❌ Failed to unsubscribe {email}")
                with btn43:
                    with st.expander("Danger Zone", expanded=False):
                        st.warning(f"⚠️ This action cannot be undone!")
                        if st.button("Delete Subscriber by Email", type="secondary", key="delete_subscriber_btn"):
                            if dbm.delete_subscriber(email):
                                st.success(f"✅ Deleted {email} successfully")
                            else:
                                st.error(f"❌ Failed to delete {email}")
    
        # Create Family Admin/Members
        st.subheader("Create Family Admin/Members")
        with st.form("create_member_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                role = st.radio("Role:", 
                    ["Family Admin", "Family Member"],
                    index=0,
                    key="new_member_role")
                new_email = st.text_input("New Email:",
                    help="Enter the email address for the new member user",
                    key="new_member_email")
            
            with col2:
                new_password = st.text_input("Password:", 
                    type="password", 
                    help="Enter a password (at least 8 characters)",
                    key="new_member_password")
                confirm_password = st.text_input("Confirm Password:", 
                    type="password", 
                    help="Confirm the password",
                    key="new_member_confirm_password")
            
            with col3:
                family_id = st.number_input("Family ID:", 
                    min_value=0,
                    step=1,
                    key="new_member_family_id")
                member_id = st.number_input("Member ID:", 
                    min_value=0,
                    step=1,
                    key="new_member_member_id")
            
            if new_password != confirm_password:
                st.error("Passwords do not match")
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                if not new_email or not new_password or not confirm_password:
                    st.error("Please enter both email and password")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long")
                else:
                    if role == "Family Admin":
                        role = dbm.User_State['f_admin']
                    else:
                        # Default to Family Member
                        role = dbm.User_State['f_member']
                    user_id = au.create_user(new_email, 
                                        new_password, 
                                        role=role,
                                        family_id=family_id,
                                        member_id=member_id)
                    if user_id:
                        st.success(f"✅ Family Admin/Member created successfully: {user_id}")
                        # The form will automatically clear on the next run
                    else:
                        st.error(f"❌ Failed to create family user")
        
        with st.expander("Danger Zone", expanded=False):
            st.warning(f"⚠️This action cannot be undone!")
            user_id = st.number_input("User ID:",
                                  min_value=1,
                                  max_value=100000,
                                  value=1)
            if st.button("Delete User by ID", type="primary"):
                if dbm.delete_user(user_id):
                    st.success(f"✅ User {user_id} deleted successfully")
                else:
                    st.error(f"❌ Failed to delete user {user_id}")

    except Exception as err:
        st.error(f"❌ An error occurred: {str(err)}")
    
# Initialize session state
cu.init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    show_page()
