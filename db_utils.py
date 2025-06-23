"""
db_utils.py - 資料庫工具模組

此模組提供與 SQLite 資料庫互動的函式，
用於管理家譜系統的資料庫操作。
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union
import csv
from dotenv import load_dotenv
import logging

# Load the environment variables from file
load_dotenv(".env")

# Configure logger for this module
log = logging.getLogger(__name__)
# Set log level from environment variable or default to WARNING
log_level = os.getenv('LOGGING', 'WARNING').upper()
log.setLevel(getattr(logging, log_level, logging.WARNING))

dbn = os.getenv("DB_NAME", "data/family.db")
db_path = os.path.join(os.path.dirname(__file__), dbn)
db_tables = {
    "users": os.getenv("TBL_USERS", "users"),
    "members": os.getenv("TBL_MEMBERS", "members"),
    "relatives": os.getenv("TBL_RELATIVES", "relatives")
    }
Subscriber_State = {
    'active': 1, 
    'pending': 0,
    'inactive': -1
    }

def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection"""
    conn = sqlite3.connect(dbn)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    初始化資料庫，建立必要的表格和觸發器（如果不存在）
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Enable foreign keys and set datetime format
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA temp_store = MEMORY")
        
        # Create user table with explicit timestamp format
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {db_tables['users']} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 0,
            l10n TEXT,
            token TEXT,
            is_admin INTEGER DEFAULT 0,
            password_hash TEXT,
            salt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)        
        
        # 建立 members 表格
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {db_tables['members']} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT,
            family_id TEXT,
            first_name TEXT,
            middle_name TEXT,
            alias TEXT,
            email TEXT,
            url TEXT,
            born DATE,
            died DATE,
            sex TEXT,
            gen_order INTEGER,
            dad_id INTEGER,
            mom_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dad_id) REFERENCES members(id),
            FOREIGN KEY (mom_id) REFERENCES members(id)
        )
        """)
        
        # 建立 relatives 表格
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {db_tables["relatives"]} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_family_id TEXT,
            original_surname TEXT,
            partner_id INTEGER,
            member_id INTEGER,
            relation TEXT,
            join_date Date,
            left_date Date,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_id) REFERENCES members(id),
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
        """)
        
        # 建立索引以提升查詢效能
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_name ON members(last_name, first_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relatives_member ON relatives(member_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relatives_partner ON relatives(partner_id)")
        
        # 建立更新時間戳的觸發器
        
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_members_timestamp
        AFTER UPDATE ON members
        FOR EACH ROW
        BEGIN
            UPDATE members SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)
        
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_relatives_timestamp
        AFTER UPDATE ON relatives
        FOR EACH ROW
        BEGIN
            UPDATE relatives SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

def add_subscriber(email, token, lang=None):
    """Add a new subscriber with pending status 
    or update existing one with active status"""
    with get_db_connection() as conn:
        try:
            if lang:
                conn.execute(f'''
                INSERT INTO {db_tables['users']} (email, token, is_active, l10n, created_at)
                VALUES (?, ?, {Subscriber_State['pending']}, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(email) DO UPDATE SET
                    is_active = {Subscriber_State['active']},
                token = excluded.token,
                l10n = excluded.l10n,
                updated_at = CURRENT_TIMESTAMP
                ''', (email, token, lang))
            else:
                conn.execute(f'''
                INSERT INTO {db_tables['users']} (email, token, is_active, created_at)
                VALUES (?, ?, {Subscriber_State['pending']}, CURRENT_TIMESTAMP)
                ON CONFLICT(email) DO UPDATE SET
                    is_active = {Subscriber_State['active']},
                token = excluded.token,
                updated_at = CURRENT_TIMESTAMP
                ''', (email, token))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_subscriber(email):
    """
    Unsubscribe an email address
    
    Args:
        email (str): The email address to unsubscribe
        
    Returns:
        bool: Returns True if the record was successfully updated, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Use 'inactive' state from Subscriber_State dictionary
            inactive_state = Subscriber_State['inactive']
            
            cursor.execute(f'''
            UPDATE {db_tables['users']} 
            SET is_active = ?, 
                updated_at = CURRENT_TIMESTAMP,
                token = NULL
            WHERE email = ?
            ''', (inactive_state, email))
            conn.commit()
            
            if cursor.rowcount > 0:
                log.info(f"Successfully unsubscribed {email}")
                return True
            else:
                log.warning(f"No user found with email {email} to unsubscribe")
                return False
    except Exception as e:
        log.error(f"Error unsubscribing {email}: {str(e)}", exc_info=True)
        return False

def verify_token(email, token):
    """Verify subscription token"""
    with get_db_connection() as conn:
        cursor = conn.execute(f'''
            SELECT id FROM {db_tables['users']} 
            WHERE email = ? AND token = ? ''',
            (email, token)
        )
        result = cursor.fetchone()
        return result is not None

def get_subscribers(state='active', lang=None):
    """
    Fetch subscribers from the database based on their status
    
    Args:
        state (str): Filter subscribers by state. 
            'active' - only active subscribers (default)
            'inactive' - only inactive subscribers
            'pending' - only pending subscribers
            'all' - all subscribers regardless of subscriber state and language 
    
    Returns:
        list: A list of dictionaries containing subscriber information.
              Each dictionary has keys: id, email, token, is_active, created_at, updated_at
    """
    # Validate status parameter
    if state not in ('active', 'inactive', 'pending', 'all'):
        raise ValueError("state must be 'active', 'inactive', 'pending', or 'all'")
    
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row  # This enables column access by name
        
        # Build the query based on status
        if state == 'all':
            cursor = conn.execute(f"""
            SELECT * FROM {db_tables['users']} 
            ORDER BY created_at DESC
        """)
        else:
            if lang:
                cursor = conn.execute(f"""
                SELECT * FROM {db_tables['users']} 
                WHERE is_active = ? AND l10n = ?
                ORDER BY created_at DESC
            """, (Subscriber_State[state], lang))
            else:
                cursor = conn.execute(f"""
                SELECT * FROM {db_tables['users']} 
                WHERE is_active = ?
                ORDER BY created_at DESC
            """, (Subscriber_State[state],))
        
        subscribers = [dict(row) for row in cursor.fetchall()]
        
        log.debug(f"Fetched {len(subscribers)} {state} subscribers with {lang} language")
        return subscribers

def get_subscriber(email):
    """
    Retrieve a single user record by email
    
    This function queries the database for a user record based on the email address.
    If a matching user is found, returns a dictionary containing the user information;
    otherwise, returns None.
    
    Args:
        email (str): The email address to query
        
    Returns:
        dict or None: A dictionary containing user information if found, None otherwise.
                     The dictionary includes the following keys:
                     - id: Unique user identifier
                     - email: Email address
                     - token: Verification token
                     - is_active: Account status (1/0/-1)
                     - l10n: Language/locale
                     - created_at: Creation timestamp
                     - updated_at: Last update timestamp
    """
    if not email or not isinstance(email, str):
        log.warning("Invalid email provided to get_user")
        return None
        
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(f"""
            SELECT * 
            FROM {db_tables['users']} 
            WHERE email = ?
        """, (email,))
        
        result = cursor.fetchone()
        if result:
            user = dict(result)
            log.debug(f"Found user: {user['email']}")
            return user
            
    log.debug(f"No user found with email: {email}")
    return None

def delete_user(user_id):
    """
    Delete a user by their ID.
    
    Args:
        user_id (int): The ID of the user to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not isinstance(user_id, int) or user_id <= 0:
        log.error(f"Invalid user ID provided for deletion: {user_id}")
        return False
        
    with get_db_connection() as conn:
        try:
            # Use parameterized query to prevent SQL injection
            sql = f"DELETE FROM {db_tables['users']} WHERE id = ?"
            log.debug(f"Executing: {sql} with user_id: {user_id}")
            
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            rows_affected = cursor.rowcount
            conn.commit()  # Commit the transaction
            
            if rows_affected > 0:
                log.info(f"Successfully deleted user with ID: {user_id}")
                return True
            else:
                log.warning(f"No user found with ID: {user_id}")
                return False
                
        except sqlite3.Error as e:
            log.error(f"Database error while deleting user ID {user_id}: {str(e)}")
            conn.rollback()
            return False
        except Exception as e:
            log.error(f"Unexpected error while deleting user ID {user_id}: {str(e)}")
            conn.rollback()
            return False

def delete_subscriber(email):
    """
    Delete a subscriber by email. 
    In fact, any user record can be deleted.
    
    Args:
        email (str): The email address of the subscriber to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not email:
        log.error("No email provided for deletion")
        return False
        
    with get_db_connection() as conn:
        try:
            # Use parameterized query to prevent SQL injection
            sql = f"DELETE FROM {db_tables['users']} WHERE email = ?"
            log.debug(f"Executing: {sql} with email: {email}")
            
            cursor = conn.cursor()
            cursor.execute(sql, (email,))
            rows_affected = cursor.rowcount
            conn.commit()  # Commit the transaction
            
            if rows_affected > 0:
                log.info(f"Successfully deleted subscriber: {email}")
                return True
            else:
                log.warning(f"No subscriber found with email: {email}")
                return False
                
        except sqlite3.Error as e:
            log.error(f"Database error while deleting subscriber {email}: {str(e)}")
            conn.rollback()
            return False
        except Exception as e:
            log.error(f"Unexpected error while deleting subscriber {email}: {str(e)}")
            conn.rollback()
            return False

def import_users_from_file(file_path: Union[str, Path], db_connection: sqlite3.Connection, table: str) -> Dict[str, Any]:
    """
    Import users from a JSON or CSV file into the users table.
    
    Args:
        file_path: Path to the JSON or CSV file containing user data
        db_connection: SQLite database connection object
        
    Returns:
        Dict with import results: {
            'success': bool,
            'imported': int,
            'skipped': int,
            'errors': List[str]
        }
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [f"File not found: {file_path}"]
        }
    
    try:
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                users = json.load(f)
                if not isinstance(users, list):
                    users = [users]  # Handle single user object
        elif file_path.suffix.lower() == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                users = list(reader)
        else:
            return {
                'success': False,
                'imported': 0,
                'skipped': 0,
                'errors': ["Unsupported file format. Please use JSON or CSV."]
            }
        
        return import_users(users, db_connection, table)
    
    except Exception as e:
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [f"Error reading file: {str(e)}"]
        }

def import_users(users: List[Dict[str, Any]], db_connection: sqlite3.Connection, table: str) -> Dict[str, Any]:
    """
    Import users into the database.
    
    Args:
        users: List of user dictionaries with required fields
        db_connection: SQLite database connection object
        
    Returns:
        Dict with import results
    """
    required_fields = {'email', 
                       'password_hash', 
                       'salt', 
                       'is_admin', 
                       'is_active',
                       'created_at',
                       'updated_at'}
    imported = 0
    skipped = 0
    errors = []
    
    cursor = db_connection.cursor()
    
    for i, user in enumerate(users, 1):
        try:
            # Check required fields
            missing_fields = required_fields - set(user.keys())
            if missing_fields:
                errors.append(f"User {i}: Missing required fields: {', '.join(missing_fields)}")
                skipped += 1
                continue
                
            # Check if user already exists
            cursor.execute(f"SELECT id FROM {table} WHERE email = ?", (user['email'],))
            if cursor.fetchone() is not None:
                errors.append(f"User {i}: User with email '{user['email']}' already exists")
                skipped += 1
                continue
            
            # Insert user
            cursor.execute(f"""
                INSERT INTO {table} (
                    email, password_hash, salt, is_admin, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user['email'],
                user['password_hash'],
                user['salt'],
                user['is_admin'],
                user['is_active'],
                user['created_at'],
                user['updated_at']
            ))
            
            imported += 1
            
        except Exception as e:
            errors.append(f"Error importing user {i} ({user['email']}): {str(e)}")
            skipped += 1
    
    if imported > 0:
        db_connection.commit()
    
    return {
        'success': len(errors) == 0,
        'imported': imported,
        'skipped': skipped,
        'errors': errors
    }

def export_users_to_file(file_path: Union[str, Path], db_connection: sqlite3.Connection, table: str) -> Dict[str, Any]:
    """
    Export users from the database to a JSON or CSV file.
    
    Args:
        file_path: Path to save the exported file (must end with .json or .csv)
        db_connection: SQLite database connection object
        
    Returns:
        Dict with export results
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        cursor = db_connection.cursor()
        cursor.execute(f"""
            SELECT id, email, password_hash, salt, is_admin, is_active, created_at, updated_at
            FROM {table}
            ORDER BY email
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'email': row[1],
                'password_hash': row[2],
                'salt': row[3],
                'is_admin': bool(row[4]),
                'is_active': bool(row[5]),
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        elif file_path.suffix.lower() == '.csv':
            if users:
                fieldnames = users[0].keys()
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(users)
        else:
            return {
                'success': False,
                'message': "Unsupported file format. Please use .json or .csv"
            }
        
        return {
            'success': True,
            'message': f"Successfully exported {len(users)} users to {file_path}",
            'file_path': str(file_path.absolute())
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f"Error exporting users: {str(e)}"
        }
        
def add_member(member_data: Dict[str, Any]) -> int:
    """
    新增成員到資料庫
    
    Args:
        member_data: 包含成員資料的字典，需要包含以下欄位：
            - last_name: 姓氏
            - first_name: 名字
            - sex: 性別
            - born: 出生日期 (YYYY-MM-DD)
            - family_id: 家族ID (可選)
            - middle_name: 中間名 (可選)
            - alias: 別名 (可選)
            - email: 電子郵件 (可選)
            - url: 個人網址 (可選)
            - died: 逝世日期 (可選)
            - gen_order: 世代序號 (可選)
            - dad_id: 父親ID (可選)
            - mom_id: 母親ID (可選)
        
    Returns:
        int: 新增的成員 ID
        
    Raises:
        ValueError: 當缺少必要欄位時
        sqlite3.Error: 當資料庫操作失敗時
    """
    required_fields = ['last_name', 'first_name', 'sex', 'born']
    missing_fields = [field for field in required_fields if field not in member_data]
    if missing_fields:
        raise ValueError(f"缺少必要欄位: {', '.join(missing_fields)}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                INSERT INTO {db_tables["members"]} (
                    last_name, family_id, first_name, middle_name, alias,
                    email, url, born, died, sex, gen_order, dad_id, mom_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                member_data.get('last_name'),
                member_data.get('family_id'),
                member_data.get('first_name'),
                member_data.get('middle_name'),
                member_data.get('alias'),
                member_data.get('email'),
                member_data.get('url'),
                member_data.get('born'),
                member_data.get('died'),
                member_data.get('sex'),
                member_data.get('gen_order'),
                member_data.get('dad_id'),
                member_data.get('mom_id')
            ))
            member_id = cursor.lastrowid
            conn.commit()
            return member_id
        except sqlite3.Error as e:
            conn.rollback()
            raise sqlite3.Error(f"新增成員失敗: {str(e)}")


def add_related_member(
    member_data: Dict[str, Any],
    original_family_id: str,
    original_surname: str,
    partner_id: int,
    relation: str,
    join_date: str,
    left_date: str = None
) -> Tuple[int, int]:
    """
    新增成員並與現有成員建立關係
    
    Args:
        member_data: 新成員的資料，參考 add_member() 的參數說明
        partner_id: 已存在成員的 ID，將與新成員建立關係
        relation: 關係類型，例如：'spouse', 'parent', 'child' 等
        join_date: 關係開始日期 (YYYY-MM-DD)
        left_date: 關係結束日期 (YYYY-MM-DD)，可選
        
    Returns:
        Tuple[int, int]: (新成員ID, 關係ID)
        
    Raises:
        ValueError: 當參數無效時
        sqlite3.Error: 當資料庫操作失敗時
    """
    if not all([member_data, partner_id, relation, join_date]):
        raise ValueError("缺少必要參數")
        
    if not isinstance(partner_id, int) or partner_id <= 0:
        raise ValueError("partner_id 必須是正整數")
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # 開始事務
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. 檢查 partner 是否存在
            cursor.execute(f"SELECT id FROM {db_tables["members"]} WHERE id = ?", (partner_id,))
            if not cursor.fetchone():
                raise ValueError(f"找不到 ID 為 {partner_id} 的成員")
            
            # 2. 新增成員
            member_id = add_member(member_data)
            
            # 3. 建立關係
            cursor.execute("""
                INSERT INTO relatives (
                    original_family_id, original_surname, partner_id, member_id, relation, join_date, left_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                original_family_id,
                original_surname,
                partner_id,
                member_id,
                relation,
                join_date,
                left_date
            ))
            
            conn.commit()
            return member_id, cursor.lastrowid
            
        except Exception as e:
            conn.rollback()
            if isinstance(e, sqlite3.Error):
                raise sqlite3.Error(f"資料庫錯誤: {str(e)}")
            raise


def update_related_member(
    relation_id: int,
    left_date: str,
    **updates
) -> bool:
    """
    更新關係資料，主要用於設置關係結束日期
    
    Args:
        relation_id: 關係ID
        left_date: 關係結束日期 (YYYY-MM-DD)
        **updates: 其他要更新的欄位
        
    Returns:
        bool: 更新是否成功
        
    Raises:
        ValueError: 當參數無效時
        sqlite3.Error: 當資料庫操作失敗時
    """
    if not relation_id or not left_date:
        raise ValueError("relation_id 和 left_date 為必要參數")
        
    if not isinstance(relation_id, int) or relation_id <= 0:
        raise ValueError("relation_id 必須是正整數")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 構建更新語句
            set_clause = "left_date = ?"
            params = [left_date]
            
            # 添加其他要更新的欄位
            for key, value in updates.items():
                if value is not None:
                    set_clause += f", {key} = ?"
                    params.append(value)
            
            # 添加 relation_id 到參數列表
            params.append(relation_id)
            
            # 執行更新
            cursor.execute(
                f"""
                UPDATE relatives 
                SET {set_clause}
                WHERE id = ?
                """,
                params
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
    except sqlite3.Error as e:
        if 'conn' in locals():
            conn.rollback()
        raise sqlite3.Error(f"更新關係資料失敗: {str(e)}")
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        raise


def get_member(member_id: int) -> Optional[Dict[str, Any]]:
    """
    根據 ID 取得成員資料
    
    Args:
        member_id: 成員 ID
        
    Returns:
        Optional[Dict[str, Any]]: 成員資料字典，如果找不到則返回 None
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {db_tables["members"]} WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_member(member_id: int, update_data: Dict[str, Any]) -> bool:
    """
    更新成員資料
    
    Args:
        member_id: 成員 ID
        update_data: 要更新的資料字典
        
    Returns:
        bool: 更新是否成功
    """
    if not update_data:
        return False
        
    set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
    values = list(update_data.values())
    values.append(member_id)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {db_tables["members"]} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_member(member_id: int) -> bool:
    """
    刪除成員
    
    Args:
        member_id: 成員 ID
        
    Returns:
        bool: 刪除是否成功
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {db_tables["members"]} WHERE id = ?", (member_id,))
        conn.commit()
        return cursor.rowcount > 0


def search_members(
    last_name: str = "",
    first_name: str = "",
    family_id: str = "",
    gen_order: int = None,
) -> List[Dict[str, Any]]:
    """
    搜尋成員
    
    Args:
        last_name: 姓氏
        first_name: 名字
        family_id: 家族 ID
        gen_order: 世代序號
        
    Returns:
        List[Dict[str, Any]]: 符合條件的成員列表
    """
    conditions = []
    params = []
    
    if last_name:
        conditions.append("last_name LIKE ?")
        params.append(f"%{last_name}%")
    if first_name:
        conditions.append("first_name LIKE ?")
        params.append(f"%{first_name}%")
    if family_id:
        conditions.append("family_id = ?")
        params.append(family_id)
    if gen_order is not None:
        conditions.append("gen_order = ?")
        params.append(gen_order)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {db_tables["members"]} WHERE {where_clause} ORDER BY last_name, first_name", params)
        return [dict(row) for row in cursor.fetchall()]


def export_to_csv(output_path: str) -> bool:
    """
    將資料庫資料匯出為 CSV 檔案
    
    Args:
        output_path: 輸出檔案路徑
        
    Returns:
        bool: 匯出是否成功
    """
    import csv
    from pathlib import Path
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with get_db_connection() as conn, open(output_path, 'w', newline='', encoding='utf-8') as f:
            cursor = conn.cursor()
            
            # 匯出 members 表格
            cursor.execute(f"SELECT * FROM {db_tables["members"]}")
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])  # 寫入欄位名稱
            writer.writerows(cursor.fetchall())
            
        return True
    except Exception as e:
        print(f"匯出 CSV 時發生錯誤: {e}")
        return False


def import_from_csv(file_path: str) -> Tuple[bool, str]:
    """
    從 CSV 檔案匯入資料到資料庫
    
    Args:
        file_path: CSV 檔案路徑
        
    Returns:
        Tuple[bool, str]: (是否成功, 訊息)
    """
    import csv
    from pathlib import Path
    
    if not Path(file_path).exists():
        return False, f"檔案不存在: {file_path}"
    
    try:
        with get_db_connection() as conn, open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # 讀取標題列
            
            # 確認必要的欄位存在
            required_fields = {'last_name', 'first_name', 'born'}
            if not required_fields.issubset(header):
                return False, f"CSV 檔案缺少必要欄位: {required_fields - set(header)}"
            
            # 開始交易
            cursor = conn.cursor()
            
            # 清空現有資料（可選，根據需求調整）
            # cursor.execute(f"DELETE FROM {db_tables["members"]}")
            
            # 插入新資料
            placeholders = ", ".join(["?"] * len(header))
            insert_sql = f"INSERT INTO {db_tables["members"]} ({', '.join(header)}) VALUES ({placeholders})"
            
            for row in reader:
                if len(row) == len(header):
                    cursor.execute(insert_sql, row)
            
            conn.commit()
            return True, "資料匯入成功"
            
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return False, f"匯入資料時發生錯誤: {str(e)}"

def update_member_when_joined(
    member_id: int,
    spouse_data: Dict[str, Any],
    relation: str,
    join_date: str,
    original_family_id: str = None,
    original_surname: str = None
) -> Tuple[int, int, int]:
    """
    create a relative for the existing member (member_id)
    and add a new member for the relative partner 
    
    Args:
        member_id: 要更新狀態的成員ID
        spouse_data: 配偶的資料，需包含以下欄位：
            - last_name: 姓氏
            - first_name: 名字
            - sex: 性別
            - born: 出生日期 (YYYY-MM-DD)
            - 其他可選欄位參考 add_member() 函數
        join_date: 日期 (YYYY-MM-DD)
        original_family_id: 配偶原家族ID (可選)
        original_surname: 配偶原姓氏 (可選)
        
    Returns:
        Tuple[int, int]: (新增的配偶ID, 關係ID)
        
    Raises:
        ValueError: 當參數無效時
        sqlite3.Error: 當資料庫操作失敗時
    """
    required_fields = ['last_name', 'first_name', 'sex', 'born']
    missing_fields = [field for field in required_fields if field not in spouse_data]
    if missing_fields:
        raise ValueError(f"缺少必要欄位: {', '.join(missing_fields)}")
        
    if not isinstance(member_id, int) or member_id <= 0:
        raise ValueError("member_id 必須是正整數")
        
    if not marriage_date:
        raise ValueError("marriage_date 為必要參數")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
        
            # 新增配偶到 members 表
            spouse_id = add_member(spouse_data)
            
            # 在 relatives 表中建立關係
            cursor.execute("""
                INSERT INTO relatives (
                    original_family_id, 
                    original_surname, 
                    partner_id, 
                    member_id, 
                    relation, 
                    join_date
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                original_family_id,
                original_surname,
                member_id,
                spouse_id,
                'spouse',
                marriage_date
            ))
                
        except Exception as e:
            conn.rollback()
            if isinstance(e, sqlite3.Error):
                raise sqlite3.Error(f"資料庫錯誤: {str(e)}")
            raise


def update_member_when_ended(
    member1_id: int,
    member2_id: int,
    relation: str,
    left_date: str
) -> Tuple[int, int]:
    """
    更新雙方的狀態並更新關係記錄
    
    Args:
        member1_id: 第一個成員的ID
        member2_id: 第二個成員的ID
        left_date: 離婚日期 (YYYY-MM-DD)
        
    Returns:
        更新的關係記錄數
        
    Raises:
        ValueError: 當參數無效時
        sqlite3.Error: 當資料庫操作失敗時
    """
    if not all([member1_id, member2_id, relation, left_date]):
        raise ValueError("所有參數均為必要")
        
    if not all(isinstance(id_, int) and id_ > 0 for id_ in [member1_id, member2_id]):
        raise ValueError("成員ID必須是正整數")
    
    if member1_id == member2_id:
        raise ValueError("兩個成員ID不能相同")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. 檢查兩個成員是否存在且狀態為 married
            cursor.execute("""
                SELECT id FROM {db_table['members']} 
                WHERE id IN (?, ?)",
                (member1_id, member2_id)
            """)
            members = cursor.fetchall()
            
            if len(members) != 2:
                found_ids = [str(m[0]) for m in members]
                raise ValueError(f"找不到指定的成員，現有成員ID: {', '.join(found_ids) if found_ids else '無'}")
            
            for member in members:
                if member[1] != 'married':
                    raise ValueError(f"成員 {member[0]} 的狀態必須為 'married'，目前為: {member[1]}")
            
            # 更新關係記錄，設置 left_date
            cursor.execute("""
                UPDATE db_tbl["relatives"] 
                SET left_date = ?
                WHERE ((partner_id = ? AND member_id = ?) 
                       OR (partner_id = ? AND member_id = ?))
                  AND relation = relation)
            """, (
                left_date,
                member1_id, member2_id,
                member2_id, member1_id
            ))
            updated_relations = cursor.rowcount
            
            if updated_relations == 0:
                raise ValueError("找不到有效的配偶關係記錄")
            
            conn.commit()
            return updated_relations
            
        except Exception as e:
            conn.rollback()
            if isinstance(e, sqlite3.Error):
                raise sqlite3.Error(f"資料庫錯誤: {str(e)}")
            raise


def update_member_when_died(
    member_id: int,
    died_date: str
) -> Tuple[int, int]:
    """
    更新成員狀態為已過世，並更新相關關係記錄
    
    Args:
        member_id: 要更新狀態的成員ID
        died_date: 過世日期 (YYYY-MM-DD)
        
    Returns:
        Tuple[int, int]: (更新的成員記錄數, 更新的關係記錄數)
        
    Raises:
        ValueError: 當參數無效時
        sqlite3.Error: 當資料庫操作失敗時
    """
    if not member_id or not died_date:
        raise ValueError("member_id 和 died_date 均為必要參數")
        
    if not isinstance(member_id, int) or member_id <= 0:
        raise ValueError("member_id 必須是正整數")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. 檢查成員是否存在
            cursor.execute(
                f"SELECT id, status FROM {db_tables["members"]} WHERE id = ?",
                (member_id,)
            )
            member = cursor.fetchone()
            
            if not member:
                raise ValueError(f"找不到 ID 為 {member_id} 的成員")
            
            cursor.execute(f"""UPDATE {db_tables["relatives"]} 
                    SET left_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE (partner_id = ? or member_id = ?
                    AND (left_date IS NULL OR left_date = '')
                    """,
                    (died_date, member_id, member_id)
                )
            updated_relations = cursor.rowcount
            
            conn.commit()
            return updated_members, updated_relations
            
        except Exception as e:
            conn.rollback()
            if isinstance(e, sqlite3.Error):
                raise sqlite3.Error(f"資料庫錯誤: {str(e)}")
            
            raise Exception(f"update_member_when_died: {e}")
        
def get_relations(id):
    """
    根據成員ID取得所有相關的親屬關係記錄
    
    此函數會查詢'relatives'表格，返回所有與指定成員ID相關的記錄
    (包括該成員作為member_id或partner_id的記錄)
    
    Args:
        member_id (int): 要查詢的成員ID
        
    Returns:
        list: 包含所有相關親屬關係記錄的列表，每個記錄以字典形式表示
              如果沒有找到相關記錄，則返回空列表
              
    Raises:
        Exception: 如果資料庫查詢過程中發生錯誤
    """
    with get_db_connection() as conn:     
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        
            cursor.execute("""
            SELECT * FROM dbm.db_tbl["relatives"] 
            WHERE member_id = ? OR partner_id = ?,
            (id,id)
            """)
        
            # 將查詢結果轉換為字典列表
            results = [dict(row) for row in cursor.fetchall()]
            return results
        
        except sqlite3.Error as e:
            # 記錄錯誤日誌
            log.debug(f"資料庫查詢錯誤: {e}")
            raise Exception(f"取得親屬關係時發生錯誤: {e}")
        
    
def get_members_when_born_in(month: int) -> List[Dict[str, Any]]:
    """
    取得指定月份出生的所有在世成員列表
    
    Args:
        month: 月份 (1-12)
        
    Returns:
        List[Dict[str, Any]]: 包含符合條件的成員資料的字典列表
        
    Raises:
        ValueError: 當月份參數無效時
        sqlite3.Error: 當資料庫操作失敗時
    """
    if not isinstance(month, int) or month < 1 or month > 12:
        raise ValueError("月份必須是 1 到 12 之間的整數")
    
    with get_db_connection() as conn:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 使用 strftime 函數提取月份進行比對
            cursor.execute(f"""
                SELECT * FROM {db_tables["members"]} 
                WHERE (died IS NULL OR died = '')
                  AND strftime('%m', born) = ?
                ORDER BY 
                    strftime('%d', born),  -- 按日期排序
                    last_name,             -- 再按姓氏排序
                    first_name             -- 最後按名字排序
            """, (f"{month:02d}",))  # 格式化為兩位數月份
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            raise sqlite3.Error(f"查詢出生月份為 {month} 月的在世成員時發生錯誤: {str(e)}")


def get_members_when_alive() -> List[Dict[str, Any]]:
    """
    取得所有在世成員的列表
    
    Returns:
        List[Dict[str, Any]]: 包含所有在世成員資料的字典列表
        
    Raises:
        sqlite3.Error: 當資料庫操作失敗時
    """
    with get_db_connection() as conn:
        try:
            conn.row_factory = sqlite3.Row  # 返回字典類型的行
            cursor = conn.cursor()
            
            # 查詢所有沒有死亡日期的成員（即仍然在世的成員）
            cursor.execute(f"""
                SELECT * FROM {db_tables["members"]} 
                WHERE (died IS NULL OR died = '')
                ORDER BY last_name, first_name
            """)
            
            # 將查詢結果轉換為字典列表
            members = []
            for row in cursor.fetchall():
                members.append(dict(row))
                
            return members
            
        except sqlite3.Error as e:
            raise sqlite3.Error(f"查詢在世成員時發生錯誤: {str(e)}")


# 初始化資料庫（如果尚未初始化）
init_db()
if __name__ == "__main__":
    # 測試資料庫連接和初始化
    print("資料庫初始化完成")
    print(f"資料庫位置: {db_path}/{dbn}")
    
    # 測試查詢在世成員
    try:
        alive_members = get_members_when_alive()
        print(f"找到 {len(alive_members)} 位在世成員")
        for member in alive_members[:5]:  # 只顯示前5位成員
            print(f"- {member.get('last_name', '')}{member.get('first_name', '')} (ID: {member.get('id')})")
        if len(alive_members) > 5:
            print(f"... 及其他 {len(alive_members) - 5} 位成員")
            
        # 假設要查詢ID為123的成員的所有關係
        relations = get_relations(123)
    
        if relations:
            print(f"找到 {len(relations)} 筆相關記錄：")
            for rel in relations:
                print(f"關係ID: {rel['id']}, 成員1: {rel['member_id']}, 成員2: {rel['partner_id']}, 關係類型: {rel['relation_type']}")
        else:
            print("沒有找到相關的關係記錄")
        
    except sqlite3.Error as e:
        print(f"錯誤: {str(e)}")

