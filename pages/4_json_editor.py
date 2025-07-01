"""
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
from admin_ui import init_session_state

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
    
    # Initialize session state for file content
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    
    # Directory selection
    dirs = {
        'Project Root': Path(__file__).parent.parent,  # Go up one level to the project root where admin_ui.py is
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
    
    # JSON editor --- from here
    st.markdown("---")
    st.subheader("Editing Area")
    # Ensure file_content is a string
    if not isinstance(st.session_state.file_content, str):
        st.session_state.file_content = "{\n    \"key\": \"value\"\n}"
    
    # Text area for editing JSON
    edited_json = st.text_area(
        "",
        value=st.session_state.file_content,
        height=600,
        key="json_editor"
    )
    
    # Update session state with edited content
    st.session_state.file_content = edited_json
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save Changes") and file_path:
            try:
                parsed_json = json.loads(edited_json)
                if save_json(file_path, parsed_json):
                    st.success(f"Saved to {file_path}")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
    
    with col2:
        if st.button("Reload") and file_path and file_path.exists():
            # Clear the current file content to force a reload
            if 'file_content' in st.session_state:
                del st.session_state.file_content
            st.session_state.reload_file = True
            st.rerun()
    
    with col3:
        if st.button("Download"):
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

    
# Initialize session state
init_session_state()
    
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
else:
    main()
