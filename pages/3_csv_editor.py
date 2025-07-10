"""
CSV Editor for Streamlit

This module provides a user interface for viewing and editing CSV files within a Streamlit application.
It includes features for:
- Browsing and selecting CSV files from different directories
- Creating new CSV files
- Editing CSV content in a data grid
- Saving changes back to files
- Reloading files to see external changes
- Downloading CSV files
- Viewing formatted data in a table
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import context_utils as cu
import os
import time

def load_csv(file_path):
    """
    Load CSV data from a file.

    Args:
        file_path (str or Path): Path to the CSV file to load

    Returns:
        DataFrame: Loaded data as a pandas DataFrame, or empty DataFrame if file doesn't exist
    """
    try:
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return pd.DataFrame()

def save_csv(file_path, df):
    """
    Save DataFrame to a CSV file.

    Args:
        file_path (str or Path): Path where the CSV file will be saved
        df (DataFrame): Data to be saved as CSV

    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return False

def main():
    st.title("CSV Editor")
    
    # Initialize session state variables
    if 'file_content' not in st.session_state:
        st.session_state.file_content = pd.DataFrame()
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'force_reload' not in st.session_state:
        st.session_state.force_reload = False
    if 'reload_file_path' not in st.session_state:
        st.session_state.reload_file_path = None
    if 'reload_file' not in st.session_state:
        st.session_state.reload_file = False
    
    # Directory selection
    dirs = {
        'Data': Path(__file__).parent.parent / "data",  # Data directory
        'Project Root': Path(__file__).parent.parent   # Project root
    }
    
    selected_dir_name = st.sidebar.selectbox(
        "Select a directory",
        list(dirs.keys()),
        index=0
    )
    
    # Get the selected directory path
    selected_dir = dirs[selected_dir_name]
    
    # File selection
    csv_files = list(selected_dir.glob("*.csv"))
    selected_file = st.sidebar.selectbox(
        "Select a CSV file",
        ["Create New..."] + [f.name for f in csv_files],
        index=0
    )
    
    # Handle new file creation
    if selected_file == "Create New...":
        new_file = st.sidebar.text_input("New filename (e.g., data.csv)")
        if new_file and not new_file.endswith('.csv'):
            new_file += '.csv'
        file_path = selected_dir / new_file if new_file else None
    else:
        file_path = selected_dir / selected_file if selected_file != "Create New..." else None
    
    def load_file_content():
        """
        Load file content into a DataFrame.

        Returns:
            DataFrame: Loaded data as a pandas DataFrame, or an empty DataFrame if the file is empty or does not exist.
        """
        try:
            if file_path and file_path.exists():
                # Read CSV with error handling for empty files
                try:
                    df = pd.read_csv(file_path)
                    if df.empty:
                        st.warning("The file is empty. Starting with an empty table.")
                        df = pd.DataFrame(columns=['Column 1'])
                except pd.errors.EmptyDataError:
                    st.warning("The file is empty. Starting with an empty table.")
                    df = pd.DataFrame(columns=['Column 1'])
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    df = pd.DataFrame(columns=['Column 1'])
            else:
                # For new files, start with one empty column
                df = pd.DataFrame(columns=['Column 1'])
            return df
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return pd.DataFrame(columns=['Column 1'])
    
    # Check if we need to load or reload the file
    force_reload = st.session_state.get('force_reload', False)
    reload_path = st.session_state.get('reload_file_path')
    file_changed = 'current_file' not in st.session_state or st.session_state.current_file != str(file_path)
    reload_needed = 'reload_file' in st.session_state and st.session_state.reload_file
    
    if 'file_content' not in st.session_state or file_changed or reload_needed or (force_reload and reload_path == str(file_path)):
        try:
            if force_reload and reload_path and Path(reload_path).exists():
                # Force reload the file
                st.session_state.file_content = pd.read_csv(reload_path)
                st.session_state.current_file = reload_path
                # Clear the reload flags
                del st.session_state.force_reload
                del st.session_state.reload_file
            else:
                # Normal load
                st.session_state.file_content = load_file_content()
                st.session_state.current_file = str(file_path) if file_path else None
            
            # Clear reload flag if it was set
            if 'reload_file' in st.session_state:
                del st.session_state.reload_file
        except Exception as e:
            st.error(f"Error loading file: {e}")
            st.session_state.file_content = pd.DataFrame(columns=['Column 1'])
    
    # Display current file path
    if file_path:
        st.sidebar.write(f"Editing: `{file_path}`")
    
    # Ensure file_content is a DataFrame
    if not isinstance(st.session_state.file_content, pd.DataFrame):
        st.session_state.file_content = pd.DataFrame(columns=['Column 1'])
    
    st.markdown("---")
    st.subheader("Editing Area")
    # Data editor - use a unique key from session state or generate a new one
    if 'editor_key' not in st.session_state:
        st.session_state.editor_key = f"editor_{file_path.name if file_path else 'new'}_{time.time()}"
    
    # Get the current content from session state
    current_content = st.session_state.file_content
    
    # Display the data editor with the current editor key
    edited_df = st.data_editor(
        current_content,
        num_rows="dynamic",
        use_container_width=True,
        key=st.session_state.editor_key
    )
    
    # Only update session state if there are actual changes
    if not current_content.equals(edited_df):
        st.session_state.file_content = edited_df
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save Changes") and file_path:
            try:
                if save_csv(file_path, edited_df):
                    st.success(f"Saved to {file_path}")
            except Exception as e:
                st.error(f"Error saving file: {e}")
    
    with col2:
        if st.button("Reload"):
            if file_path and file_path.exists():
                try:
                    # Load the file content first
                    new_content = pd.read_csv(file_path)
                    
                    # Generate a unique key based on timestamp to force refresh
                    st.session_state.editor_key = f"editor_{file_path.name}_{time.time()}"
                    
                    # Update the content and current file
                    st.session_state.file_content = new_content
                    st.session_state.current_file = str(file_path)
                    
                    # Force a rerun to update the editor
                    st.rerun()
                except Exception as e:
                    st.error(f"Error reloading file: {e}")
            else:
                st.warning("No valid file selected or file doesn't exist")
    
    with col3:
        if st.button("Download"):
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=file_path.name if file_path else "data.csv",
                mime="text/csv"
            )
    
    # Display data in a table
    with st.expander("View Formatted Table"):
        if not edited_df.empty:
            st.dataframe(edited_df, use_container_width=True)
        else:
            st.info("No data to display")

    
# Initialize session state
cu.init_session_state()
    
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    main()
