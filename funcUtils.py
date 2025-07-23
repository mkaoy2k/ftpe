import os
from dotenv import load_dotenv  # pip install python-dotenv
import json
import streamlit as st  # pip install streamlit
import datetime as dt
import traceback

def get_function_name():
    """取得目前函數名稱"""
    return traceback.extract_stack(None, 2)[0][2]

def get_languages():
    """
    Get I18N supported languages
    
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

# Helper function to format timestamps
def format_timestamp(ts) -> str:
    """
    格式化時間戳記為易讀字串
    
    Args:
        ts: 時間戳記 (可以是 datetime 對象或字串)
                        
    Returns:
        str: 格式化後的時間字串，若解析失敗則返回原始字串
    """
    if not ts:
        return "Never"
                        
    # 如果是 datetime 對象，直接格式化
    if isinstance(ts, dt.datetime):
        return ts.strftime('%Y-%m-%d %H:%M:%S')
                        
    # 如果是字串，嘗試解析
    ts_str = str(ts)
    try:
        # 嘗試 ISO 8601 格式 (包含 'T' 分隔符)
        if 'T' in ts_str:
            date_time = dt.fromisoformat(ts_str.replace('Z', '+00:00'))
        # 嘗試空格分隔的格式
        else:
            # 嘗試帶有微秒的格式
            for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
                try:
                    date_time = dt.datetime.strptime(ts_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return ts_str  # 所有格式都失敗，返回原始字串
            return date_time.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError) as e:
        return ts_str  # 解析失敗，返回原始字串

def test_func():
    print(f"Function name: {get_function_name()}")
                        
if __name__ == '__main__':
    """
    Function test code
    """
    test_func()