"""
Family Management Page

This module provides a Streamlit interface for managing family members including
searching, adding, updating, and deleting member information.
"""
import context_utils as cu
import auth_utils as au
import streamlit as st
import db_utils as dbm
from ftpe_ui import search_members_page

# Hide the default navigation for members
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import funcUtils as fu

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
        "sex_options": ["Male", "Female", "Other"],
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
        "warning": "This action cannot be undone!",
        "confirm_title": "The following member will be deleted:",
        "confirm_checkbox": "I confirm that I want to delete this member",
        "confirm_button": "Confirm Deletion",
        "success": "Successfully deleted member: {name}",
        "error": "Error deleting member"
    }
}

def search_families_page() -> None:
    """
    Display the family search page with filters and results.
    """
    st.subheader("Search Families")
    
    # Initialize session state for search results
    if 'family_search_results' not in st.session_state:
        st.session_state.family_search_results = []
    
    # Search form
    with st.form("family_search_form"):
        st.subheader("Search Criteria")
        
        # Create two rows of search fields
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        with row1_col1:
            name = st.text_input("Family Name")
        
        with row1_col2:
            family_id = st.number_input(
                "Family ID",
                min_value=1,
                value=1,
                step=1
            )
            
        with row2_col1:
            background = st.text_area("background contains")
            
        with row2_col2:
            url = st.text_input("website url")
        
        # add a search button
        submitted = st.form_submit_button("search")
    
    # process search when form is submitted
    if submitted:
        with st.spinner("searching..."):
            # get all families (since we don't have a search_families function yet)
            all_families = dbm.get_families()
            
            # filter based on search criteria
            results = []
            for family in all_families:
                # skip if name doesn't match
                if name and name.lower() not in family.get('name', '').lower():
                    continue
                    
                # skip if family_id doesn't match
                if family_id and str(family_id) != str(family.get('id', '')):
                    continue
                    
                # skip if background doesn't contain the search term
                if (background and 
                    background.lower() not in family.get('background', '').lower()):
                    continue
                    
                # skip if url doesn't contain the search term
                if (url and 
                    url.lower() not in family.get('url', '').lower()):
                    continue
                    
                results.append(family)
            
            # store results in session state
            st.session_state.family_search_results = results
    
    # display search results if available
    if st.session_state.family_search_results:
        st.subheader("search results")
        
        # convert results to dataframe for better display
        df = pd.dataframe(st.session_state.family_search_results)
        
        # rename columns for better display
        if not df.empty:
            # select and reorder columns
            all_fields = ['id', 'name', 'background', 'url', 'created_at', 'updated_at']
            
            # Filter out columns that don't exist in the results
            existing_fields = [col for col in all_fields if col in df.columns]
            df = df[existing_fields]
            
            # Display the data in a table
            st.dataframe(
                df,
                column_config={
                    'id': 'ID',
                    'name': '家族名稱',
                    'background': '背景',
                    'url': '網站',
                    'created_at': '建立時間',
                    'updated_at': '更新時間'
                },
                hide_index=True,
                use_container_width=True,
                column_order=all_fields
            )
            
            # Show result count with bigger and bolder text
            st.markdown(f"<p style='font-size: 1.2em; font-weight: bold;'>Found {len(df)} records</p>", unsafe_allow_html=True)
    
    # No results message
    elif submitted:
        st.info("No matching families found")

def add_family_page() -> None:
    """Display the form to add a new family."""
    st.subheader("Add New Family")
    
    with st.form("add_family_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Family Name*", "")
            url = st.text_input(
                "Family Website",
                "",
                placeholder="https://example.com"
            )
        
        with col2:
            background = st.text_area(
                "Family Background/History",
                "",
                height=100,
                help="Enter any relevant family history or background information"
            )
        
        # Form submission button
        submitted = st.form_submit_button("Add Family")
        
        if submitted:
            # Validate required fields
            if not name:
                st.error("Family name is required")
                return
                
            try:
                # Prepare family data
                family_data = {
                    'name': name.strip(),
                    'background': background.strip() if background else None,
                    'url': url.strip() if url else None
                }
                
                # Add family to database
                family_id = dbm.add_or_update_family(
                    family_data, update=False)
                
                if family_id:
                    st.success(f"✅ Successfully added family: {name} (ID: {family_id})")
                    
                    # Clear form
                    st.rerun()
                else:
                    st.error(f"❌Failed to add family. Please try again.")
                
            except ValueError as ve:
                st.error(f"❌ Validation error: {str(ve)}")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

def update_family_page() -> None:
    """Display the form to update an existing family."""
    st.subheader("Update Family")
    
    # Get family ID to update
    family_id = st.number_input(
        "Enter Family ID to update",
        min_value=1,
        step=1
    )
    
    if family_id:
        # Get family data
        family = dbm.get_family(family_id)
        
        if not family:
            st.warning(f"⚠️ {UI_TEXTS["update"]["not_found"]}")
            return
            
        with st.form(f"update_family_form_{family_id}"):
            st.subheader(f"Update Family: {family.get('name', '')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Family Name*", family.get('name', ''))
                
                # Display creation/update timestamps as read-only
                created_at = family.get('created_at', 'N/A')
                updated_at = family.get('updated_at', 'N/A')
                
                st.caption(f"Created: {created_at}")
                st.caption(f"Last Updated: {updated_at}")
                
            with col2:
                url = st.text_input(
                    "Family Website",
                    family.get('url', ''),
                    placeholder="https://example.com"
                )
            
            background = st.text_area(
                "Family Background/History",
                family.get('background', ''),
                height=150,
                help="Enter any relevant family history or background information"
            )
            
            submitted = st.form_submit_button("Update Family")
            
            if submitted:
                # Validate required fields
                if not name:
                    st.error(f"❌Family name is required")
                    return
                    
                try:
                    # Prepare update data with only changed fields
                    update_data = {}
                    
                    if name != family.get('name'):
                        update_data['name'] = name.strip()
                    if background != family.get('background'):
                        update_data['background'] = background.strip() if background else None
                    if url != family.get('url'):
                        update_data['url'] = url.strip() if url else None
                    
                    if update_data:
                        # Add the update flag to indicate this is an update
                        update_data['id'] = family_id
                        
                        # Update family in database
                        updated_id = dbm.add_or_update_family(update_data, update=True)
                        
                        if updated_id:
                            st.success(f"✅ {UI_TEXTS["update"]["success"]} {name} (ID: {family_id})")
                            st.rerun()
                        else:
                            st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str("Failed to update family. Please try again.")}")
                    else:
                        st.info(f"No changes detected.")
                        
                except ValueError as ve:
                    st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str(ve)}")
                except Exception as e:
                    st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str(e)}")

def search_relations_page() -> None:
    """
    Display the relation search page with filters and results.
    """
    st.subheader("Search Relations")
    
    # Initialize session state for search results
    if 'relation_search_results' not in st.session_state:
        st.session_state.relation_search_results = []
    
    # Search form
    with st.form("relation_search_form"):
        st.subheader("Search Criteria")
        
        # Create two rows of search fields
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        with row1_col1:
            member_id = st.text_input("Member ID")
            relation_type = st.selectbox(
                "Relation Type",
                ["", "spouse", "parent", "child", "sibling"],
                index=0
            )
        
        with row1_col2:
            partner_id = st.number_input(
                "Partner ID",
                min_value=0,
                step=1,
                value=0
            )
            original_family_id = st.number_input(
                "Original Family ID",
                min_value=1,
                value=1,
                step=1
            )
            
        with row2_col1:
            join_date_from = st.date_input(
                "Join Date From",
                value=None,
                format="YYYY-MM-DD"
            )
        
        with row2_col2:
            join_date_to = st.date_input(
                "Join Date To",
                value=None,
                format="YYYY-MM-DD"
            )
        
        # Add a search button
        submitted = st.form_submit_button("Search")
    
    # Process search when form is submitted
    if submitted:
        with st.spinner("Searching..."):
            try:
                # Get all relations
                all_relations = dbm.get_relations()
                
                # Filter based on search criteria
                results = []
                for relation in all_relations:
                    # Skip if member_id doesn't match
                    if member_id and str(relation.get('member_id', '')) != str(member_id):
                        continue
                        
                    # Skip if partner_id doesn't match (ensure both are compared as integers)
                    if partner_id and int(relation.get('partner_id', 0)) != int(partner_id):
                        continue
                        
                    # Skip if relation type doesn't match
                    if relation_type and relation.get('relation', '').lower() != relation_type.lower():
                        continue
                        
                    # Skip if original_family_id doesn't match
                    if (original_family_id and 
                        str(relation.get('original_family_id', '')) != str(original_family_id)):
                        continue
                    
                    # Filter by join date range if provided
                    if join_date_from or join_date_to:
                        try:
                            join_date = datetime.strptime(relation.get('join_date', ''), '%Y-%m-%d').date()
                            if join_date_from and join_date < join_date_from:
                                continue
                            if join_date_to and join_date > join_date_to:
                                continue
                        except (ValueError, TypeError):
                            # Skip if date parsing fails
                            continue
                    
                    results.append(relation)
                
                # Store results in session state
                st.session_state.relation_search_results = results
                
            except Exception as e:
                st.error(f"Error searching relations: {str(e)}")
                st.session_state.relation_search_results = []
    
    # Display search results if available
    if st.session_state.relation_search_results:
        st.subheader("Search Results")
        
        # Convert results to DataFrame for better display
        df = pd.DataFrame(st.session_state.relation_search_results)
        
        # Rename columns for better display
        if not df.empty:
            # Select and reorder columns
            all_fields = [
                'id', 'member_id', 'partner_id', 'relation', 
                'original_family_id', 'original_name', 'join_date', 'end_date',
                'created_at', 'updated_at'
            ]
            
            # Filter out columns that don't exist in the results
            existing_fields = [col for col in all_fields if col in df.columns]
            df = df[existing_fields]
            
            # Display the data in a table
            st.dataframe(
                df,
                column_config={
                    'id': 'ID',
                    'member_id': 'Member ID',
                    'partner_id': 'Related Member ID',
                    'relation': 'Relation Type',
                    'original_family_id': 'Original Family ID',
                    'original_name': 'Original Name',
                    'join_date': 'Start Date',
                    'end_date': 'End Date',
                    'created_at': 'Created At',
                    'updated_at': 'Updated At'
                },
                hide_index=True,
                use_container_width=True,
                column_order=all_fields
            )
            
            # Show result count with bigger and bolder text
            st.markdown(f"<p style='font-size: 1.2em; font-weight: bold;'>Found {len(df)} records</p>", unsafe_allow_html=True)
    
    # No results message
    elif submitted:
        st.info("No matching relation records found")

def add_relation_page() -> None:
    """
    Display the form to add a new relation between members.
    """
    st.subheader("Add New Relation")
    
    with st.form("add_relation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            member_id = st.number_input(
                "Member ID*",
                min_value=1,
                step=1,
                help="ID of the first member in the relationship"
            )
            
            relation_type = st.selectbox(
                "Relation Type*",
                ['spouse', 'parent', 'child', 'sibling', 'other'],
                help="Type of relationship between the members"
            )
            
            join_date = st.date_input(
                "Start Date",
                value=date.today(),
                help="When this relationship began"
            )
            
        with col2:
            partner_id = st.number_input(
                "Partner ID*",
                min_value=1,
                step=1,
                value=1,
                help="ID of the second member in the relationship"
            )
            
            original_family_id = st.number_input(
                "Original Family ID",
                min_value=0,
                step=1,
                value=0,
                help="Original family ID if applicable"
            )
            
            end_date = st.date_input(
                "End Date (optional)",
                value=None,
                help="If this relationship has ended, when it ended"
            )
        
        # Additional fields
        original_name = st.text_input("Original Name (if different)", "")
        dad_name = st.text_input("Father's Name (if applicable)", "")
        mom_name = st.text_input("Mother's Name (if applicable)", "")
        
        submitted = st.form_submit_button("Add Relation")
        
        if submitted:
            # Validate required fields
            if not member_id or not partner_id or not relation_type:
                st.error(f"❌ {UI_TEXTS["add"]["error_required"]}")
                return
                
            try:
                # Prepare relation data
                relation_data = {
                    'member_id': member_id,
                    'partner_id': partner_id,
                    'relation': relation_type,
                    'join_date': join_date.isoformat(),
                    'original_family_id': original_family_id if original_family_id > 0 else None,
                    'original_name': original_name if original_name else None,
                    'dad_name': dad_name if dad_name else None,
                    'mom_name': mom_name if mom_name else None
                }
                
                # Add end date if provided
                if end_date:
                    relation_data['end_date'] = end_date.isoformat()
                
                # Add relation to database
                relation_id = dbm.add_or_update_relation(relation_data, update=False)
                
                if relation_id:
                    st.success(f"✅ {UI_TEXTS["add"]["success"]} {relation_id}")
                    # Clear form
                    st.rerun()
                else:
                    st.error(f"❌ {UI_TEXTS["add"]["error_generic"]} {str("Failed to add relation. Please check the member IDs and try again.")}")
                
            except ValueError as ve:
                st.error(f"❌ {UI_TEXTS["add"]["error_generic"]} {str(ve)}")
            except sqlite3.Error as se:
                st.error(f"❌ {UI_TEXTS["add"]["error_generic"]} {str(se)}")
            except Exception as e:
                st.error(f"❌ {UI_TEXTS["add"]["error_generic"]} {str(e)}")

def update_relation_page() -> None:
    """
    Display the form to update an existing relation.
    """
    st.subheader("Update Relation")
    
    # Get relation ID to update
    relation_id = st.number_input(
        "Enter Relation ID to update",
        min_value=1,
        step=1
    )
    
    if relation_id:
        # Get relation data
        relation = dbm.get_relation(relation_id)
        
        if not relation:
            st.warning(f"⚠️ {UI_TEXTS["update"]["not_found"]}")
            return
            
        with st.form(f"update_relation_form_{relation_id}"):
            st.subheader(f"Update Relation: {relation_id}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                member_id = st.number_input(
                    "Member ID*",
                    min_value=1,
                    step=1,
                    value=relation.get('member_id', 1),
                    help="ID of the first member in the relationship"
                )
                
                relation_type = st.selectbox(
                    "Relation Type*",
                    ['spouse', 'parent', 'child', 'sibling', 'other'],
                    index=['spouse', 'parent', 'child', 'sibling', 'other'].index(relation.get('relation', 'spouse')),
                    help="Type of relationship between the members"
                )
                
                # Safely handle different date input types
                join_date_value = relation.get('join_date')
                if join_date_value is None:
                    default_date = date.today()
                elif isinstance(join_date_value, str):
                    try:
                        default_date = datetime.strptime(join_date_value, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        default_date = date.today()
                elif hasattr(join_date_value, 'date'):  # Already a date/datetime object
                    default_date = join_date_value.date() if hasattr(join_date_value, 'date') else date.today()
                else:
                    default_date = date.today()
                
                join_date = st.date_input(
                    "Start Date",
                    value=default_date,
                    help="When this relationship began"
                )
                
            with col2:
                partner_id = st.number_input(
                    "Partner ID*",
                    min_value=1,
                    step=1,
                    value=relation.get('partner_id', 1),
                    help="ID of the second member in the relationship"
                )
                
                original_family_id = st.number_input(
                    "Original Family ID",
                    min_value=0,
                    step=1,
                    value=relation.get('original_family_id', 0),
                    help="Original family ID if applicable"
                )
                
                end_date_value = relation.get('end_date')
                end_date = st.date_input(
                    "End Date (optional)",
                    value=datetime.strptime(end_date_value, '%Y-%m-%d').date() if end_date_value else None,
                    help="If this relationship has ended, when it ended"
                )
            
            # Additional fields
            original_name = st.text_input(
                "Original Name (if different)",
                relation.get('original_name', '')
            )
            dad_name = st.text_input(
                "Father's Name (if applicable)",
                relation.get('dad_name', '')
            )
            mom_name = st.text_input(
                "Mother's Name (if applicable)",
                relation.get('mom_name', '')
            )
            
            # Display timestamps
            created_at = relation.get('created_at', 'N/A')
            updated_at = relation.get('updated_at', 'N/A')
            st.caption(f"Created: {created_at}")
            st.caption(f"Last Updated: {updated_at}")
            
            submitted = st.form_submit_button("Update Relation")
            
            if submitted:
                # Validate required fields
                if not member_id or not partner_id or not relation_type:
                    st.error(f"❌ {UI_TEXTS["update"]["error_required"]}")
                    return
                    
                try:
                    # Prepare update data with only changed fields
                    update_data = {}
                    
                    # Check which fields have changed
                    if member_id != relation.get('member_id'):
                        update_data['member_id'] = member_id
                    if partner_id != relation.get('partner_id'):
                        update_data['partner_id'] = partner_id
                    if relation_type != relation.get('relation'):
                        update_data['relation'] = relation_type
                    
                    # Handle dates
                    join_date_str = join_date.isoformat()
                    if join_date_str != relation.get('join_date'):
                        update_data['join_date'] = join_date_str
                    
                    if end_date:
                        end_date_str = end_date.isoformat()
                        if end_date_str != relation.get('end_date'):
                            update_data['end_date'] = end_date_str
                    
                    # Handle optional fields
                    optional_fields = {
                        'original_family_id': original_family_id if original_family_id > 0 else None,
                        'original_name': original_name if original_name else None,
                        'dad_name': dad_name if dad_name else None,
                        'mom_name': mom_name if mom_name else None
                    }
                    
                    for field, value in optional_fields.items():
                        if value != relation.get(field):
                            update_data[field] = value
                    
                    if update_data:
                        # Add the ID for the update
                        update_data['id'] = relation_id
                        
                        # Update relation in database
                        updated_id = dbm.add_or_update_relation(update_data, update=True)
                        
                        if updated_id:
                            st.success(f"✅ {UI_TEXTS["update"]["success"]} {relation_id}")
                            st.rerun()
                        else:
                            st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str("Failed to update relation (ID: {relation_id}). Please try again.")}")
                    else:
                        st.info(f"No changes detected for relation (ID: {relation_id}).")
                        
                except ValueError as ve:
                    st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str(ve)}")
                except sqlite3.Error as se:
                    st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str(se)}")
                except Exception as e:
                    st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str(e)}")

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
            family_id = st.number_input(
                UI_TEXTS["add"]["family_id"],
                min_value=0,
                step=1,
                value=0
            )
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
            if not name or not gen_order or not born:
                st.error(f"❌ {UI_TEXTS["add"]["error_required"]}")
                return
                
            try:
                member_data = {
                    'name': name,
                    'sex': sex[0].upper() if sex else None,
                    'born': born,
                    'family_id': int(family_id) if int(family_id) >= 0 else 0,
                    'alias': alias if alias else None,
                    'email': email if email else None,
                    'url': url if url else 'https://',
                    'gen_order': int(gen_order) if int(gen_order) > 0 else 0,
                }
                
                # Add new or update existing family member
                member_id = dbm.add_or_update_member(member_data, False)
                if member_id:
                    if email and password:
                        # Create user in users table
                        user_id = au.create_user(email, password,
                                role=dbm.User_State['f_member'],
                                member_id=member_id)
                        if user_id:
                            st.success(f"✅ {UI_TEXTS["add"]["success"]} {member_id}")
                    else:
                        st.info(UI_TEXTS["add"]["no_update_user_table"])
                else:
                    error = "Failed to add member"
                    st.error(f"❌ {UI_TEXTS["add"]["error_generic"]} {error}")
                
            except Exception as e:
                st.error(f"❌ {UI_TEXTS["add"]["error_generic"]} {str(e)}")

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
            st.warning(f"⚠️ {UI_TEXTS["update"]["not_found"]}")
            return
            
        with st.form(f"update_form_{member_id}"):
            st.subheader(UI_TEXTS["update"]["form_title"].format(
                name=member.get('name', ''),
                id=member_id
            ))
            
            # Three-column layout for better organization
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Basic Information
                st.subheader("Basic Information")
                name = st.text_input(
                    "Name*",
                    member.get('name', '')
                )
                
                alias = st.text_input(
                    "Alias",
                    member.get('alias', '')
                )
                
                # Gender selection with proper value mapping
                gender_options = UI_TEXTS["add"]["sex_options"]
                gender_values = [gender_options[0][0], 
                                 gender_options[1][0], 
                                 gender_options[2][0]]
                
                # Get current gender, default to 'M' if invalid
                current_sex = str(member.get('sex', 'M')).strip().upper()
                if current_sex not in gender_values:
                    current_sex = 'M'
                
                # Get the index of current gender for the selectbox
                current_index = gender_values.index(current_sex)
                
                # Display the selectbox and get the selected index
                selected_index = st.selectbox(
                    "Gender*",
                    gender_options,
                    index=current_index
                )
                
                # Get the corresponding value from our values list
                sex = gender_values[gender_options.index(selected_index)]
                
            with col2:
                # Dates and Family
                st.subheader("Dates & Family")
                born = st.text_input(
                    "Birth Date* (YYYY-MM-DD)",
                    member.get('born', '')
                )
                
                died = st.text_input(
                    "Death Date (YYYY-MM-DD)",
                    member.get('died', '')
                )
                
                family_id = st.number_input(
                    "Family ID",
                    min_value=0,
                    step=1,
                    value=member.get('family_id', '')
                )
                
                # Ensure gen_order is an integer
                try:
                    gen_order_value = int(member.get('gen_order', 0))
                except (ValueError, TypeError):
                    gen_order_value = 0
                    
                gen_order = st.number_input(
                    "Generation",
                    min_value=0,
                    step=1,
                    value=gen_order_value
                )
                
            with col3:
                # Contact and Relations
                st.subheader("Contact & Relationships")
                email = st.text_input(
                    "Email",
                    member.get('email', '')
                )
                
                url = st.text_input(
                    "Personal Website",
                    member.get('url', 'https://')
                )
                
                dad_id = st.number_input(
                    "Father ID",
                    min_value=0,
                    step=1,
                    value=member.get('dad_id', 0)
                )
                
                mom_id = st.number_input(
                    "Mother ID",
                    min_value=0,
                    step=1,
                    value=member.get('mom_id', 0)
                )
            
            submitted = st.form_submit_button(UI_TEXTS["update"]["submit_button"])
            
            if submitted:
                # Validate required fields
                if not name or not gen_order or not born:
                    st.error(UI_TEXTS["add"]["error_required"])
                    return
                    
                try:
                    update_data = {
                        'name': name,
                        'sex': sex if sex else None,
                        'born': born,
                        'died': died if died else '0000-01-01',
                        'family_id': int(family_id) if int(family_id) >= 0 else 0,
                        'alias': alias if alias else None,
                        'email': email if email else None,
                        'url': url if url else None,
                        'gen_order': gen_order if gen_order > 0 else 0,
                        'dad_id': int(dad_id) if int(dad_id) >= 0 else 0,
                        'mom_id': int(mom_id) if int(mom_id) >= 0 else 0
                    }
                    
                    # Remove unchanged fields
                    for key in list(update_data.keys()):
                        if key in member and update_data[key] == member[key]:
                            del update_data[key]
                    
                    if update_data:
                        success = dbm.update_member(member_id, update_data)
                        if success:
                            st.success(f"✅ {UI_TEXTS["update"]["success"]}")
                        else:
                            st.warning(f"⚠️ {UI_TEXTS["update"]["no_changes"]}")
                    else:
                        st.info(f"⚠️ {UI_TEXTS["update"]["nothing_to_update"]}")
                            
                except Exception as e:
                    st.error(f"❌ {UI_TEXTS["update"]["error_generic"]} {str(e)}")

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
            st.warning(f"⚠️ {UI_TEXTS["delete"]["not_found"]}")
            return
            
        st.warning(f"⚠️ {UI_TEXTS["delete"]["warning"]}")
        
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
                        st.success(f"✅ {UI_TEXTS["delete"]["success"]}")
                    else:
                        st.error(f"❌ {UI_TEXTS["delete"]["error"]}")
                except Exception as e:
                    st.error(f"Error deleting member: {str(e)}")

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
        
        # Add a refresh button
        refresh = st.button("🔃 Refresh")
    
    with col2:
        st.write("")
    
    try:
        # Get members born in the selected month
        members = dbm.get_members_when_born_in(month_number)
        
        if not members:
            st.info(f"⚠️ {UI_TEXTS["birthday"]["not_found"]}")
            return
            
        # Create a DataFrame for display
        df = pd.DataFrame([{
            'ID': m.get('id', ''),
            'Name': m.get('name', ''),
            'Gender': 'Male' if m.get('gender') == 'M' else 'Female',
            'Birthday': fu.format_timestamp(m.get('born')),
            'Email': m.get('email', '')
        } for m in members])
        
        # Display the results
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
        
        # Add export button with improved error handling
        if st.button("💾 Export Birthday List"):
            try:
                # Ensure we have data to export
                if df.empty:
                    st.warning("No data available to export.")
                    return
                    
                # Generate CSV with proper encoding for Chinese characters
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                
                # Create download button with proper file naming
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"birthday_list_{selected_month.lower()}_{datetime.now().year}.csv",
                    mime="text/csv",
                    help=f"Download birthday list for {selected_month} {datetime.now().year}"
                )
                
                # Show success message
                st.success(f"✅ Successfully exported {len(df)} records for {selected_month}")
                
            except Exception as e:
                st.error(f"❌ Error generating CSV: {str(e)}")
                st.exception(e)  # For debugging
    except Exception as e:
        st.error(f"❌ Error exporting birthday list: {str(e)}")
        st.exception(e)  # For debugging

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
        st.page_link("pages/6_show_3G.py", label="Show 3 Generations", icon="👥")            
        st.divider()
            
        # Add logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    
    # Main content area
    st.title("Family Tree Management")
    
    # Main tab groups
    tab1, tab2, tab3 = st.tabs(["👥 Member Management", "🏠 Family Management", "🔗 Relations Management"])
    
    with tab1:  # Member Management
        st.header("👥 Member Management")
        
        # Define the tab labels explicitly to ensure we have the correct number
        member_tab_labels = [
            "🔍 Search Members",
            "➕ Add Member",
            "✏️ Update Member",
            "🗑️ Delete Member",
            "🎂 Birthday Calendar"
        ]
        
        # Create tabs with explicit labels
        member_tabs = st.tabs(member_tab_labels)
        
        # Map each tab to its corresponding function
        with member_tabs[0]:  # Search Members
            search_members_page()
            
        with member_tabs[1]:  # Add Member
            add_member_page()
            
        with member_tabs[2]:  # Update Member
            update_member_page()
            
        with member_tabs[3]:  # Delete Member
            delete_member_page()
            
        with member_tabs[4]:  # Birthday Calendar
            birthday_of_the_month_page()
    
    with tab2:  # Family Management
        st.header("🏠 Family Management")
        family_tab1, family_tab2, family_tab3 = st.tabs(["🔍 Search Families", "➕ Add Family", "✏️ Update Family"])
        
        with family_tab1:  # Search Families
            search_families_page()
            
        with family_tab2:  # Add Family
            add_family_page()
            
        with family_tab3:  # Update Family
            update_family_page()
    
    with tab3:  # Relations Management
        st.header("🔗 Relations Management")
        relation_tab1, relation_tab2, relation_tab3 = st.tabs(["🔍 Search Relations", "➕ Add Relation", "✏️ Update Relation"])
        
        with relation_tab1:  # Search Relations
            search_relations_page()
            
        with relation_tab2:  # Add Relation
            add_relation_page()
            
        with relation_tab3:  # Update Relation
            update_relation_page()

# Initialize session state and app context
if 'app_context' not in st.session_state:
    cu.init_session_state()
    st.session_state.app_context = cu.init_context()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    main()