"""
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


JSON Editor for Streamlit

This module provides a user interface for viewing and editing JSON files within a Streamlit application.
It includes features for:
- Browsing and selecting JSON files from different directories
- Creating new JSON files
- Editing JSON content with syntax highlighting
- Saving changes back to files
- Reloading files to see external changes
- Downloading JSON files
- Viewing formatted JSON output
"""

import streamlit as st
import json
import os
from pathlib import Path
import context_utils as cu
import db_utils as dbm

def load_json(file_path):
    """
    Load JSON data from a file.

    Args:
        file_path (str or Path): Path to the JSON file to load

    Returns:
        dict: Parsed JSON data as a dictionary, or empty dict if file doesn't exist or is invalid
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError:
        st.error("Error: Invalid JSON file")
        return {}

def save_json(file_path, data):
    """
    Save data to a JSON file.

    Args:
        file_path (str or Path): Path where the JSON file will be saved
        data (dict): Data to be saved as JSON

    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return False

def main():
    st.title("JSON Editor")
    # --- Sidebar --- from here
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
                unsafe_allow_html=True)
            cu.update_context({
                'email_user': st.session_state.user_email
            })
        
        if st.session_state.user_state != dbm.User_State['p_admin']:
            st.subheader("Navigation")
            st.page_link("ftpe_ui.py", label="Home", icon="🏠")
            st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
            st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
            st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="📊")
            st.page_link("pages/6_show_3G.py", label="Show 3 Generations", icon="👥")
            st.page_link("pages/7_show_related.py", label="Show Related", icon="👨‍👩‍👧‍👦")
            if st.session_state.user_state == dbm.User_State['f_admin']:
                st.page_link("pages/2_famMgmt.py", label="Family Management", icon="🌲")
        
        # Add logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True, key="json_editor_logout"):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
        # Directory selection
        dirs = {
            'Project Root': Path(__file__).parent.parent,  # Go up one level to the project root where ftpe_ui.py is
            'Data': Path(__file__).parent.parent / "data"
        }
    
        selected_dir_name = st.sidebar.selectbox(
            "Select a directory",
            list(dirs.keys()),
            index=0
        )
    
        # Get the selected directory path
        selected_dir = dirs[selected_dir_name]
    
        # File selection
        json_files = list(selected_dir.glob("*.json"))
        selected_file = st.sidebar.selectbox(
            "Select a JSON file",
            ["Create New..."] + [f.name for f in json_files],
            index=0
        )
    
        # Handle new file creation
        if selected_file == "Create New...":
            new_file = st.sidebar.text_input("New filename (e.g., data.json)")
            if new_file and not new_file.endswith('.json'):
                new_file += '.json'
            file_path = selected_dir / new_file if new_file else None
        else:
            file_path = selected_dir / selected_file if selected_file != "Create New..." else None
    
        # Handle file loading and reloading
        file_changed = ('current_file' not in st.session_state or 
                       str(file_path) != st.session_state.get('current_file'))
    
        if (file_changed or 'reload_file' in st.session_state) and file_path and file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    st.session_state.file_content = f.read()
                st.session_state.current_file = str(file_path)
                if 'reload_file' in st.session_state:
                    del st.session_state.reload_file
            except Exception as e:
                st.error(f"Error loading file: {e}")
                st.session_state.file_content = "{\n    \"key\": \"value\"\n}"
        elif not file_path or not file_path.exists():
            st.session_state.file_content = "{\n    \"key\": \"value\"\n}"
    
        # Display current file path
        if file_path:
            st.sidebar.write(f"Editing: `{file_path}`")
    # --- Sidebar --- to here
    
    # --- Main Content --- from here
    st.subheader("Editing Area")
    # Ensure file_content is a string
    if not isinstance(st.session_state.file_content, str):
        st.session_state.file_content = "{\n    \"key\": \"value\"\n}"
    
    # Text area for editing JSON
    edited_json = st.text_area(
        "Edit JSON content:",
        value=st.session_state.file_content,
        height=600,
        key="json_editor"
    )
    
    # Update session state with edited content
    st.session_state.file_content = edited_json
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save Changes", type="primary") and file_path:
            try:
                parsed_json = json.loads(edited_json)
                if save_json(file_path, parsed_json):
                    st.success(f"Saved to {file_path}")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
    
    with col2:
        if st.button("Reload", type="secondary") and file_path and file_path.exists():
            # Clear the current file content to force a reload
            if 'file_content' in st.session_state:
                del st.session_state.file_content
            st.session_state.reload_file = True
            st.rerun()
    
    with col3:
        if st.button("Download", type="secondary"):
            st.download_button(
                label="Download JSON",
                data=edited_json,
                file_name=file_path.name if file_path else "data.json",
                mime="application/json"
            )
    
    # Display JSON in expandable section --- to here
    with st.expander("View Formatted JSON"):
        try:
            parsed = json.loads(edited_json)
            st.json(parsed)
        except json.JSONDecodeError:
            st.error("Invalid JSON")
    # --- Main Content --- to here
    
# Initialize session state
cu.init_session_state()
    
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    # Initialize session state for file content
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    main()
