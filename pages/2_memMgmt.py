"""
Member Management Page

This module provides a Streamlit interface for managing family members including
searching, adding, updating, and deleting member information.
"""

import streamlit as st

# Hide the default navigation for members
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)
import pandas as pd
from typing import List, Dict, Any
from admin_ui import init_session_state
import db_utils as dbm
import tempfile
import os

# Constants for UI text
UI_TEXTS = {
    "search": {
        "title": "Member Search",
        "form_title": "Search Members",
        "name": "Name",
        "alias": "Alias",
        "family_id": "Family ID",
        "generation": "Generation",
        "birth_date": "Birth Date",
        "birth_date_placeholder": "YYYY or YYYY-MM or YYYY-MM-DD",
        "death_date": "Death Date",
        "death_date_placeholder": "YYYY or YYYY-MM or YYYY-MM-DD",
        "search_button": "Search",
        "searching": "Searching...",
        "results_title": "Search Results",
        "no_results": "No matching members found",
        "results_count": "Found {count} records"
    },
    "add": {
        "title": "Add Member",
        "name": "Full Name*",
        "sex": "Gender*",
        "sex_options": ["", "Male", "Female", "Other"],
        "birth_date": "Birth Date (YYYY-MM-DD)*",
        "birth_date_placeholder": "e.g., 1990-01-01",
        "family_id": "Family ID",
        "alias": "Alias",
        "generation": "Generation",
        "email": "Email",
        "url": "Website",
        "submit_button": "Add Member",
        "success": "Member added successfully! Member ID: {id}",
        "error_required": "Please fill in all required fields (marked with *)",
        "error_generic": "Error adding member: {error}"
    },
    "update": {
        "title": "Update Member",
        "member_id_prompt": "Enter Member ID to update",
        "not_found": "Member not found",
        "form_title": "Update Member: {name} (ID: {id})",
        "submit_button": "Update Information",
        "success": "Member information updated successfully!",
        "no_changes": "No changes were made (data was not modified)",
        "nothing_to_update": "No changes to update"
    },
    "delete": {
        "title": "Delete Member",
        "member_id_prompt": "Enter Member ID to delete",
        "not_found": "Member not found",
        "warning": "⚠️ Warning: This action cannot be undone!",
        "confirm_title": "The following member will be deleted:",
        "confirm_checkbox": "I confirm that I want to delete this member",
        "confirm_button": "Confirm Deletion",
        "success": "Successfully deleted member: {name}",
        "error": "Error deleting member"
    },
    "common": {
        "app_title": "Member Functions",
        "navigation": ["Search", "Add", 
                       "Update", "Delete", 
                       "Import", "Export"
                    ]
    },
    "import": {
        "title": "Import Members",
        "description": "Upload a CSV file to import member data.",
        "file_uploader_label": "Choose a CSV file",
        "import_button": "Import Members",
        "no_file": "Please select a file to import",
        "file_type_error": "Only CSV files are supported"
    },
    "export": {
        "title": "Export Members",
        "description": "Export all members to a CSV file.",
        "filename": "members_export",
        "export_button": "Export Members",
        "success": "Successfully exported {count} members to {filename}",
        "error": "Error exporting members: {error}",
        "download_button": "Download CSV"
    }
}

def search_members_page() -> None:
    """
    Display the member search page with filters and results.
    """
    st.subheader(UI_TEXTS["search"]["title"])
    
    # Initialize session state for search results
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    # Search form
    with st.form("search_form"):
        st.subheader(UI_TEXTS["search"]["form_title"])
        
        # Create two rows of search fields
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        
        with row1_col1:
            name = st.text_input(UI_TEXTS["search"]["name"], "")
        with row1_col2:
            born = st.text_input(
                UI_TEXTS["search"]["birth_date"],
                "",
                placeholder=UI_TEXTS["search"]["birth_date_placeholder"]
            )
        with row1_col3:
            gen_order = st.number_input(
                UI_TEXTS["search"]["generation"],
                min_value=0,
                step=1,
                value=0
            )
        with row2_col1:
            alias = st.text_input(UI_TEXTS["search"]["alias"], "")
        with row2_col2:
            died = st.text_input(
                UI_TEXTS["search"]["death_date"],
                "",
                placeholder=UI_TEXTS["search"]["death_date_placeholder"]
            )
        with row2_col3:
            family_id = st.text_input(UI_TEXTS["search"]["family_id"], "")

        
        # Search button
        submitted = st.form_submit_button(UI_TEXTS["search"]["search_button"])
        
        if submitted:
            with st.spinner(UI_TEXTS["search"]["searching"]):
                # Execute search
                results = dbm.search_members(
                    name=name if name else "",
                    alias=alias if alias else "",
                    family_id=family_id if family_id else "",
                    gen_order=gen_order if gen_order > 0 else None,
                    born=born if born else "",
                    died=died if died else ""
                )
                st.session_state.search_results = results
    
    # Display search results
    if st.session_state.search_results:
        st.subheader(UI_TEXTS["search"]["results_title"])
        
        # Prepare data for display
        df = pd.DataFrame(st.session_state.search_results)
        
        # Define column order
        column_order = ['id', 'name', 'alias', 'sex', 'born', 'gen_order', 'family_id']
        display_columns = [col for col in column_order if col in df.columns]
        
        # Display data table
        st.dataframe(
            df[display_columns],
            column_config={
                'id': 'ID',
                'name': 'Name',
                'alias': 'Alias',
                'sex': 'Gender',
                'born': 'Birth Date',
                'gen_order': 'Generation',
                'family_id': 'Family ID'
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Show result count
        st.caption(UI_TEXTS["search"]["results_count"].format(count=len(df)))
    
    # No results message
    elif submitted:
        st.info(UI_TEXTS["search"]["no_results"])

def add_member_page() -> None:
    """Display the form to add a new member."""
    st.subheader(UI_TEXTS["add"]["title"])
    
    with st.form("add_member_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(UI_TEXTS["add"]["name"], "")
            sex = st.selectbox(
                UI_TEXTS["add"]["sex"],
                UI_TEXTS["add"]["sex_options"],
                index=0
            )
            born = st.text_input(
                UI_TEXTS["add"]["birth_date"],
                "",
                placeholder=UI_TEXTS["add"]["birth_date_placeholder"]
            )
            family_id = st.text_input(UI_TEXTS["add"]["family_id"], "")
            
        with col2:
            alias = st.text_input(UI_TEXTS["add"]["alias"], "")
            gen_order = st.number_input(
                UI_TEXTS["add"]["generation"],
                min_value=0,
                step=1,
                value=0
            )
            email = st.text_input(UI_TEXTS["add"]["email"], "")
            url = st.text_input(UI_TEXTS["add"]["url"], "")
        
        submitted = st.form_submit_button(UI_TEXTS["add"]["submit_button"])
        
        if submitted:
            # Validate required fields
            if not name or not sex or not born:
                st.error(UI_TEXTS["add"]["error_required"])
                return
                
            try:
                member_data = {
                    'name': name,
                    'sex': sex[0].upper() if sex else None,  # Store as M/F/O
                    'born': born,
                    'family_id': family_id if family_id else None,
                    'alias': alias if alias else None,
                    'email': email if email else None,
                    'url': url if url else None,
                    'gen_order': gen_order if gen_order > 0 else None
                }
                
                # Add member to database
                member_id = dbm.add_member(member_data)
                st.success(UI_TEXTS["add"]["success"].format(id=member_id))
                
            except Exception as e:
                st.error(UI_TEXTS["add"]["error_generic"].format(error=str(e)))

def update_member_page() -> None:
    """Display the form to update an existing member."""
    st.subheader(UI_TEXTS["update"]["title"])
    
    # Get member ID to update
    member_id = st.number_input(
        UI_TEXTS["update"]["member_id_prompt"],
        min_value=1,
        step=1
    )
    
    if member_id:
        # Get member data
        member = dbm.get_member(member_id)
        
        if not member:
            st.warning(UI_TEXTS["update"]["not_found"])
            return
            
        with st.form(f"update_form_{member_id}"):
            st.subheader(UI_TEXTS["update"]["form_title"].format(
                name=member.get('name', ''),
                id=member_id
            ))
            
            # Two-column layout
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    UI_TEXTS["add"]["name"],
                    member.get('name', '')
                )
                
                # Convert stored gender to index
                sex_mapping = {'M': 0, 'F': 1, 'O': 2}
                current_sex = member.get('sex', '').upper()
                sex_index = sex_mapping.get(current_sex, 0)
                
                sex = st.selectbox(
                    UI_TEXTS["add"]["sex"],
                    UI_TEXTS["add"]["sex_options"][1:],  # Skip empty option
                    index=sex_index
                )
                
                born = st.text_input(
                    UI_TEXTS["add"]["birth_date"],
                    member.get('born', '')
                )
                
                family_id = st.text_input(
                    UI_TEXTS["add"]["family_id"],
                    member.get('family_id', '')
                )
                
            with col2:
                alias = st.text_input(
                    UI_TEXTS["add"]["alias"],
                    member.get('alias', '')
                )
                
                gen_order = st.number_input(
                    UI_TEXTS["add"]["generation"],
                    min_value=0,
                    step=1,
                    value=member.get('gen_order', 0)
                )
                
                email = st.text_input(
                    UI_TEXTS["add"]["email"],
                    member.get('email', '')
                )
                
                url = st.text_input(
                    UI_TEXTS["add"]["url"],
                    member.get('url', '')
                )
            
            submitted = st.form_submit_button(UI_TEXTS["update"]["submit_button"])
            
            if submitted:
                # Validate required fields
                if not name or not sex or not born:
                    st.error(UI_TEXTS["add"]["error_required"])
                    return
                    
                try:
                    update_data = {
                        'name': name,
                        'sex': sex[0].upper() if sex else None,  # Store as M/F/O
                        'born': born,
                        'family_id': family_id if family_id else None,
                        'alias': alias if alias else None,
                        'email': email if email else None,
                        'url': url if url else None,
                        'gen_order': gen_order if gen_order > 0 else None
                    }
                    
                    # Remove unchanged fields
                    for key in list(update_data.keys()):
                        if key in member and update_data[key] == member[key]:
                            del update_data[key]
                    
                    if update_data:
                        success = update_member(member_id, update_data)
                        if success:
                            st.success(UI_TEXTS["update"]["success"])
                        else:
                            st.warning(UI_TEXTS["update"]["no_changes"])
                    else:
                        st.info(UI_TEXTS["update"]["nothing_to_update"])
                            
                except Exception as e:
                    st.error(f"Error updating member: {str(e)}")

def delete_member_page() -> None:
    """Display the interface for deleting a member."""
    st.subheader(UI_TEXTS["delete"]["title"])
    
    # Get member ID to delete
    member_id = st.number_input(
        UI_TEXTS["delete"]["member_id_prompt"],
        min_value=1,
        step=1
    )
    
    if member_id:
        # Get member data
        member = dbm.get_member(member_id)
        
        if not member:
            st.warning(UI_TEXTS["delete"]["not_found"])
            return
            
        st.warning(UI_TEXTS["delete"]["warning"])
        
        # Display member data for confirmation
        st.subheader(UI_TEXTS["delete"]["confirm_title"])
        st.json(member)
        
        # Confirm deletion
        confirm = st.checkbox(UI_TEXTS["delete"]["confirm_checkbox"])
        
        if confirm:
            if st.button(
                UI_TEXTS["delete"]["confirm_button"],
                type="primary"
            ):
                try:
                    success = dbm.delete_member(member_id)
                    if success:
                        st.success(UI_TEXTS["delete"]["success"].format(
                            name=member.get('name', '')
                        ))
                    else:
                        st.error(UI_TEXTS["delete"]["error"])
                except Exception as e:
                    st.error(f"Error deleting member: {str(e)}")


def import_members_page() -> None:
    """Display the interface for importing members from a CSV file."""
    st.subheader(UI_TEXTS["import"]["title"])
    st.write(UI_TEXTS["import"]["description"])
    
    uploaded_file = st.file_uploader(
        UI_TEXTS["import"]["file_uploader_label"],
        type=["csv"]
    )
    
    if st.button(UI_TEXTS["import"]["import_button"], type="primary"):
        if uploaded_file is not None:
            try:
                # Save the uploaded file to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Import the members
                success, message = dbm.import_members_from_csv(tmp_file_path)
                
                # Clean up the temporary file
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    st.warning(f"Warning: Could not remove temporary file: {str(e)}")
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
                    
            except Exception as e:
                st.error(str(e))
        else:
            st.warning(UI_TEXTS["import"]["no_file"])


def export_members_page() -> None:
    """Display the interface for exporting members to a CSV file."""
    st.subheader(UI_TEXTS["export"]["title"])
    st.write(UI_TEXTS["export"]["description"])
    
    # Get a default filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"{UI_TEXTS['export']['filename']}_{timestamp}.csv"
    
    # Let user customize the filename
    filename = st.text_input(
        "Filename",
        value=default_filename
    )
    
    if st.button(UI_TEXTS["export"]["export_button"], type="primary"):
        try:
            # Create a temporary file for the export
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file_path = tmp_file.name
            
            # Export the members
            success = dbm.export_members_to_csv(tmp_file_path)
            
            if success:
                # Count the number of exported members
                with open(tmp_file_path, 'r', encoding='utf-8') as f:
                    # Subtract 1 for the header row
                    count = sum(1 for _ in f) - 1
                
                # Create a download button for the file
                with open(tmp_file_path, 'rb') as f:
                    st.download_button(
                        label=UI_TEXTS["export"]["download_button"],
                        data=f,
                        file_name=filename,
                        mime='text/csv',
                    )
                
                st.success(UI_TEXTS["export"]["success"].format(
                    count=count,
                    filename=filename
                ))
                
                # Clean up the temporary file after the user has downloaded it
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    st.warning(f"Warning: Could not remove temporary file: {str(e)}")
            else:
                st.error(UI_TEXTS["export"]["error"].format(error="Export failed"))
                
        except Exception as e:
            st.error(UI_TEXTS["export"]["error"].format(error=str(e)))
            
            # Clean up the temporary file if it exists
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except Exception as cleanup_error:
                    st.warning(f"Warning: Could not remove temporary file: {str(cleanup_error)}")


# Authentication functions
def show_login_form() -> bool:
    """Display login form and handle authentication."""
    with st.sidebar:
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if au.verify_member(email, password):
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.user_state = dbm.User_State['member']
                    st.rerun()
                else:
                    st.error("Invalid email or password")
        return False

# Main application
def main() -> None:
    """Main application entry point."""
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_form()
        return
        
    # Sidebar with user info and page links
    with st.sidebar:
        st.sidebar.title("Member Sidebar")

        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
            
        # Page Navigation Links
        st.subheader("Navigation")
        st.page_link("admin_ui.py", label="Home", icon="🏠")
        st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="🌲")
            
        st.divider()
            
        # Sidebar - Member User Management
        st.subheader("Member User Management")
        with st.expander("Create/Update Member User", expanded=False):
            with st.form("member_user_form"):
                st.subheader("Member User")
                email = st.text_input("Email", key="member_email", 
                                   help="Enter the email address for the member user")
                new_password = st.text_input("Password", type="password", key="new_password",
                                          help="Enter a password (at least 8 characters)")
                confirm_password = st.text_input("Confirm Password", type="password", 
                                               key="confirm_password")
                
                if st.form_submit_button("Save Member User"):
                    if not email or not fu.validate_email(email):
                        st.error("Please enter a valid email address")
                    elif not new_password:
                        st.error("Please enter a password")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    else:
                        success, message = au.create_member_user(email, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                                    
        # Add logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    
    # Main content area
    st.title("Member Management")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(UI_TEXTS["common"]["navigation"])
    
    with tab1:  # Search Members
        search_members_page()
        
    with tab2:  # Add Member
        add_member_page()
        
    with tab3:  # Update Member
        update_member_page()
        
    with tab4:  # Delete Member
        delete_member_page()
        
    with tab5:  # Import Members
        import_members_page()
        
    with tab6:  # Export Members
        export_members_page()
    

# Initialize session state
init_session_state()
    
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
else:
    main()