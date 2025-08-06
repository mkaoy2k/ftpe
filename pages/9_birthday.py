
"""
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


Birthday of the Month Page
"""
import os
import context_utils as cu
import streamlit as st
import db_utils as dbm
import pandas as pd
from datetime import datetime
import funcUtils as fu
import email_utils as eu

UI_TEXTS = {
    "birthday": {
        "member_not_found": "No members found for the selected month",
        "saved": "Birthday list saved in {file} successfully!",
        "error": "Error saving birthday list: {error}",
        "downloaded": "Birthday list downloaded in {file} successfully!",
        "error_download": "Error downloading birthday list: {error}",
        "published": "Birthday list published to {receivers} successfully!",
        "error_publish": "Error publishing birthday list: {error}"
    }
}

def birthday_of_the_month_page():
    """Display members born in a specific month."""
    st.header("🎂 Birthday Calendar")
    
    # Get current month as default
    current_month = datetime.now().month
    
    # Create two columns for month selection and display
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Month selection dropdown
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        selected_month = st.selectbox(
            "Select Month", 
            options=months, 
            index=current_month-1,
            format_func=lambda x: f"{x}"
        )
        month_number = months.index(selected_month) + 1
    
    with col2:
        st.write("")
    
    if st.button("Query"):
        try:
            # Get members born in the selected month
            members = dbm.get_members_when_born_in(month_number)
            
            if not members:
                message = f"⚠️ {UI_TEXTS['birthday']['member_not_found']}"
                st.warning(message)
                return
            
            # Create a list to hold all member data
            member_data = []
            
            # Process each member and collect their data
            for m in members:
                if m.get('sex') == 'M':
                    gender = 'Male'
                elif m.get('sex') == 'F':
                    gender = 'Female'
                else:
                    gender = 'Unknown'
                
                member_data.append({
                    'ID': m.get('id', ''),
                    'Name': m.get('name', ''),
                    'Gender': gender,
                    'Birthday': fu.format_timestamp(m.get('born')),
                    'Email': m.get('email', '')
                })
        
            # Create DataFrame from the collected data
            df = pd.DataFrame(member_data)
            
            # Ensure all date columns are strings
            date_columns = ['Birthday']
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str)
        
            # save to csv, created in the dir_path, specified in the context fss
            csv_file = f"{st.session_state.app_context['fss']['dir_path']}/birthday_list_{selected_month.lower()}_{datetime.now().year}.csv"
            # Display the results first
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'ID': st.column_config.NumberColumn('ID'),
                    'Name': st.column_config.TextColumn('Name'),
                    'Gender': st.column_config.TextColumn('Gender'),
                    'Birthday': st.column_config.TextColumn('Birthday'),
                    'Email': st.column_config.TextColumn('Email')
                }
            )
            
            # Save to CSV
            try:
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                message = f"✅ {UI_TEXTS['birthday']['saved'].format(file=csv_file)}"
                st.info(message)
            except Exception as e:
                message = f"❌ {UI_TEXTS['birthday']['error']}: {str(e)}"
                st.error(message)
           
            # Create a row with two columns for the buttons
            if not df.empty:
                st.write("")
                
                # Define callback functions
                def on_publish():
                    try:
                        # Create email publisher object
                        publisher = eu.EmailPublisher(eu.Config.MAIL_USERNAME, eu.Config.MAIL_PASSWORD)
                        
                        # Filter out None or empty email addresses
                        recipients = [m.get('email') for m in members if m.get('email')]
                        
                        if not recipients:
                            st.error("⚠️ No valid email addresses found to send to")
                            return
                        
                        # Rest of the email sending code...
                        text_content = """Wishing you a wonderful birthday celebration!
                        May this special day bring you joy and happiness!

                        Best regards,
                        Your Family Team"""
                        
                        # Create HTML content with animated birthday card
                        html_content = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
        .birthday-card {
            font-family: 'Arial', sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #fff6f6 0%, #f8e8ff 100%);
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        .birthday-title {
            font-family: 'Dancing Script', cursive;
            font-size: 36px;
            color: #e91e63;
            margin: 20px 0;
            animation: bounce 2s infinite;
        }
        .birthday-message {
            font-size: 16px;
            color: #333;
            line-height: 1.6;
            margin: 20px 0;
        }
        .balloon {
            display: inline-block;
            width: 40px;
            height: 50px;
            background: #ff4081;
            border-radius: 50%;
            position: relative;
            margin: 0 5px;
            animation: float 3s ease-in-out infinite;
        }
        .balloon:before {
            content: '';
            position: absolute;
            width: 2px;
            height: 50px;
            background: #999;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
        }
        .balloon:nth-child(2n) {
            background: #3f51b5;
            animation-delay: 0.3s;
        }
        .balloon:nth-child(3n) {
            background: #4caf50;
            animation-delay: 0.6s;
        }
        .balloon:nth-child(4n) {
            background: #ff9800;
            animation-delay: 0.9s;
        }
        @keyframes float {
            0%, 100% {
                transform: translateY(0) rotate(-2deg);
            }
            50% {
                transform: translateY(-20px) rotate(2deg);
            }
        }
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-20px);
            }
            60% {
                transform: translateY(-10px);
            }
        }
        .signature {
            margin-top: 30px;
            font-style: italic;
            color: #666;
        }
    </style>
    <div class="birthday-card">
        <div class="balloon"></div>
        <div class="balloon"></div>
        <div class="balloon"></div>
        <div class="balloon"></div>
                
        <h1 class="birthday-title">Happy Birthday!</h1>
                
        <div class="birthday-message">
            <p>Wishing you a wonderful birthday celebration!</p>
            <p>May this special day bring you joy and happiness!</p>
        </div>
                
        <div class="signature">
            <p>Best regards,<br>Your Family Team</p>
        </div>
    </div>
    """
                        
                        # Check if the attached b'day card file exists
                        card_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bday.html")
                        if not os.path.exists(card_file):
                            st.error(f"❌ {card_file} not found.")
                            return
                        
                        # Send email with the animated birthday card
                        publisher.publish_email(
                            subject=f"🎉 Happy Birthday Celebrations - {selected_month} {datetime.now().year}",
                            text=text_content,
                            html=html_content,
                            attached_file=card_file,
                            recipients=recipients
                        )
                        st.success(f"✅ Successfully sent birthday emails to {len(recipients)} recipients")
                    except Exception as e:
                        st.error(f"❌ Failed to send emails: {str(e)}")
                
                def on_download():
                    try:
                        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_data,
                            file_name=f"birthday_list_{selected_month.lower()}_{datetime.now().year}.csv",
                            mime="text/csv",
                            key="download_csv"
                        )
                        st.success(f"✅ Birthday list ready for download")
                    except Exception as e:
                        st.error(f"❌ Failed to prepare download: {str(e)}")
                
                # Create buttons with callbacks
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📧 Publish Birthday List", 
                               use_container_width=True, 
                               type="primary",
                               on_click=on_publish):
                        pass  # Callback handles the action
                
                with col2:
                    if st.button("💾 Download Birthday List", 
                               use_container_width=True, 
                               type="secondary",
                               on_click=on_download):
                        pass  # Callback handles the action
        except Exception as e:
            message = f"❌ {UI_TEXTS['birthday']['error'].format(error=str(e))}"
            st.session_state.birthday_message = message
            st.error(message)

def sidebar() -> None:
    """Sidebar application entry point."""

    # Sidebar --- from here
    with st.sidebar:
        if st.session_state.user_state == dbm.User_State['p_admin']:
            # Show default navigation for padmin users
            if 'user_email' in st.session_state and st.session_state.user_email:
                st.markdown(
                    f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin: 1rem 0;'>"
                    f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                    "</div>",
                    unsafe_allow_html=True)
                cu.update_context({
                    'email_user': st.session_state.user_email
                })
                
                # Add logout button at the bottom for admin
                if st.button("Logout", type="primary", use_container_width=True, key="fam_mgmt_admin_logout"):
                    st.session_state.authenticated = False
                    st.session_state.user_email = None
                    st.rerun()
        else:
            # For non-admin users
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
                    unsafe_allow_html=True)
                cu.update_context({
                    'email_user': st.session_state.user_email
                })
            
            st.subheader("Navigation")
            st.page_link("ftpe_ui.py", label="Home", icon="🏠")
            st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
            st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
            st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="📊")
            st.page_link("pages/6_show_3G.py", label="Show 3 Generations", icon="👥")
            st.page_link("pages/7_show_related.py", label="Show Related", icon="👨‍👩‍👧‍👦")
            if st.session_state.user_state == dbm.User_State['f_admin']:
                st.page_link("pages/8_caseMgmt.py", label="Case Management", icon="📋")
                st.page_link("pages/2_famMgmt.py", label="Family Management", icon="🌲")
            
            # Add logout button at the bottom for non-admin users
            if st.button("Logout", type="primary", use_container_width=True, key="fam_mgmt_user_logout"):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.rerun()
    
def main():
    """Main application entry point."""
    st.title("🎂 Birthday of the Month")
    
    # Main Page --- frome here
    birthday_of_the_month_page()
        
# Initialize session state and app context
cu.init_session_state()

if 'app_context' not in st.session_state:
    st.session_state.app_context = cu.init_context()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    sidebar()
    main()