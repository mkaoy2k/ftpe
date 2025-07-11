"""
Member Management Page

This module provides a Streamlit interface for managing family members including
searching, adding, updating, and deleting member information.
"""
import context_utils as cu
import auth_utils as au
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
import db_utils as dbm
import tempfile
import os
import time

# Constants for UI text
UI_TEXTS = {
    "search": {
        "title": "Search Family Members",
        "form_title": "Search Criteria",
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
        "title": "Add Family Member",
        "name": "Full Name*",
        "sex": "Gender*",
        "sex_options": ["", "Male", "Female", "Other"],
        "birth_date": "Birth Date (YYYY-MM-DD)*",
        "birth_date_placeholder": "e.g., 1990-01-01",
        "family_id": "Family ID",
        "alias": "Alias",
        "generation": "Generation",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Confirm Password",
        "url": "Website",
        "submit_button": "Add Member",
        "success": "Member added successfully! Member ID: {id}",
        "no_update_user_table": "User table not updated. Please update manually.",
        "error_required": "Please fill in all required fields (marked with *)",
        "error_generic": "Error adding member: {error}"
    },
    "update": {
        "title": "Update Family Member",
        "member_id_prompt": "Enter Member ID to update",
        "not_found": "Member not found",
        "form_title": "Update Member: {name} (ID: {id})",
        "submit_button": "Update Information",
        "success": "Member information updated successfully!",
        "no_changes": "No changes were made (data was not modified)",
        "nothing_to_update": "No changes to update"
    },
    "delete": {
        "title": "Delete Family Member",
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
        "app_title": "Family Member Management",
        "navigation": ["Search-Members", "Add-Member", 
                       "Update-Member", "Delete-Member" 
                    ]
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
            gen_order = st.number_input(
                UI_TEXTS["add"]["generation"],
                min_value=0,
                step=1,
                value=0
            )
        with col2:
            alias = st.text_input(UI_TEXTS["add"]["alias"], "")
            
            email = st.text_input(UI_TEXTS["add"]["email"], "")
            password = st.text_input(UI_TEXTS["add"]["password"], "", type="password")
            confirm_password = st.text_input(UI_TEXTS["add"]["confirm_password"], "", type="password")
            if password != confirm_password:
                st.error(UI_TEXTS["add"]["error_password_match"])
                return
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
                
                # Add new or update existing family member
                member_id = dbm.add_or_update_member(member_data, True)
                if member_id:
                    if email and password:
                        # Create user in users table
                        user_id = au.create_user(email, password,
                                role=dbm.User_State['f_member'],
                                member_id=member_id)
                        if user_id:
                            st.success(UI_TEXTS["add"]["success"].format(id=member_id))
                    else:
                        st.info(UI_TEXTS["add"]["no_update_user_table"])
                else:
                    st.error(UI_TEXTS["add"]["error_generic"].format(error="Failed to add member"))
                
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

def main() -> None:
    """Main application entry point."""
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_form()
        return
        
    # Sidebar with login button, page links, and logout button
    with st.sidebar:
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
        
        st.subheader("Navigation")
        st.page_link("ftpe_ui.py", label="Home", icon="🏠")
        st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
        st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
        st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="📊")
            
        st.divider()
            
        # Add logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    
    # Main content area
    st.title("Family Tree Management")
    context = st.session_state.get('app_context', cu.init_context())
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(UI_TEXTS["common"]["navigation"])
    
    with tab1:  # Search Members
        search_members_page()
        
    with tab2:  # Add Member
        add_member_page()
        
    with tab3:  # Update Member
        update_member_page()
        
    with tab4:  # Delete Member
        delete_member_page()

# Initialize session state
cu.init_session_state()
    
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    main()