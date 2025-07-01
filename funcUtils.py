import os
from dotenv import load_dotenv  # pip install python-dotenv
import json
import streamlit as st  # pip install streamlit


def get_languages():
    """
    Get supported languages
    
    Returns:
        list: List of supported languages
    """
    load_dotenv(".env")
    f_l10n = os.getenv("L10N_FILE", "L10N.json")
    
    # Read L10N.json which contains all supported languages
    with open(f_l10n) as f:
        data = f.read()
    js = json.loads(data)
    
    return list(js.keys())

@st.cache_data(ttl=300)
def load_L10N(base=None):
    """
    Load supported localization dictionary
    
    Args:
        base (str, optional): Base directory
    
    Returns:
        dict: Dictionary containing all supported language localizations
    """
    load_dotenv(".env")
    f_l10n = os.getenv("L10N_FILE", "L10N.json")
    
    # Read L10N.json which contains all supported languages
    with open(f_l10n) as f:
        data = f.read()
    js = json.loads(data)
    
    dl10n = {}
    for key, fl in js.items():
        with open(fl) as f:
            data = f.read()
        d = json.loads(data)
        dl10n[key] = d
    
    return dl10n


@st.cache_data(ttl=300)
def get_1st_mbr_dict(df, mem, born, base=None):
    """
    Find the first record in the DataFrame that matches the given conditions
    
    Args:
        df (pd.DataFrame): DataFrame to search
        mem (str): Member name
        born (int): Birth year
        base (str, optional): Base directory
    
    Returns:
        tuple: (index, member_dict)
            index: Record index
            member_dict: Member data dictionary
    
    Raises:
        FileNotFoundError: If no record matches the given conditions
    """
    filter = f"Name == @mem and Born == @born"
    try:
        rec = df.query(filter)
        if rec.empty:
            raise FileNotFoundError("No record matches the given conditions")
    except Exception as e:
        raise
    
    # Remove duplicate records, keep only the first one
    rec = rec[0:1]
    idx, member = rec.to_dict('index').popitem()
    return idx, member


if __name__ == '__main__':
    """
    Function test code
    """
