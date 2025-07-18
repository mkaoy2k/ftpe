"""
此腳本用於更新 'members' 表中的成員父母關係。

它會從 'mirrors' 表中讀取每個成員的父母姓名，這些成員由 gen_order,born 和 name 標識。
然後，它會為每個成員的父母尋找唯一匹配的 member_id，
並在 'members' 表中更新 dad_id 和 mom_id。

如果找不到唯一匹配，則會跳過該成員並印出重複的姓名。
"""

import sqlite3
from typing import Dict, List, Optional
from pathlib import Path
import db_utils as dbm
import logging
from datetime import datetime

# Create a unique log file for each run with timestamp
LOG_FILE = f"test_{Path(__file__).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)
DB_PATH = 'data/family.db'

class MemberParentUpdater:
    def __init__(self, db_path: str = DB_PATH):
        """
        初始化 MemberParentUpdater 類
        
        Args:
            db_path: 數據庫文件路徑
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"數據庫文件不存在: {db_path}")
        
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        """實現上下文管理器協議的進入方法"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """實現上下文管理器協議的退出方法"""
        self.close()
    
    def connect(self):
        """連接到數據庫"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # 使用列名訪問結果
            self.cursor = self.conn.cursor()
            logger.info(f"成功連接到數據庫: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"連接數據庫時出錯: {e}")
            raise
    
    def close(self):
        """關閉數據庫連接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("數據庫連接已關閉")
    
    def get_members_with_parents(self) -> List[Dict]:
        """
        從 mirrors 表中獲取需要更新父母的成員列表
        
        Returns:
            包含成員信息的字典列表，每個字典包含:
            Order, Born, Name, Dad, Mom    
        """
        try:
            query = f"""
            SELECT "Order", Born, Name, Dad, Mom
            FROM {dbm.db_tables['mirrors']}
            WHERE CAST(Relation AS INTEGER) = {dbm.Member_Relation['bio']} 
            AND (Dad IS NOT NULL OR Mom IS NOT NULL)
            """
            self.cursor.execute(query)
            
            members = []
            for row in self.cursor.fetchall():
                members.append(dict(row))
            
            logger.info(f"從 {dbm.db_tables['mirrors']} 表獲取到 {len(members)} 個需要更新父母的成員")
            return members
            
        except sqlite3.Error as e:
            logger.error(f"查詢 {dbm.db_tables['mirrors']} 表時出錯: {e}")
            raise
    
    def find_member_id(self, name: str, born: str = None, gen_order: int = None) -> Optional[int]:
        """
        根據姓名、出生日期和世代順序查找成員 ID
        
        Args:
            name: 成員姓名
            born: 出生日期 (YYYY-MM-DD)
            gen_order: 世代順序
            
        Returns:
            如果找到唯一匹配的成員，返回其 ID；否則返回 None
        """
        if not name:
            return None
            
        try:
            query = f"""
            SELECT id FROM {dbm.db_tables['members']} 
            WHERE name = ?
            """
            params = [name]
            
            if born:
                query += " AND born = ?"
                params.append(born)
            
            if gen_order is not None:
                query += " AND gen_order = ?"
                params.append(gen_order)
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if len(results) == 1:
                return results[0][0]
            elif len(results) > 1:
                logger.warning(f"找到多個匹配的成員: 姓名={name}, 出生日期={born}, 世代順序={gen_order}")
                return None
            else:
                return None
                
        except sqlite3.Error as e:
            logger.error(f"查找成員 ID 時出錯: {e}")
            return None
    
    def update_member_parents(self, member_id: int, dad_id: int = None, mom_id: int = None) -> bool:
        """
        更新成員的父母 ID
        
        Args:
            member_id: 要更新的成員 ID
            dad_id: 父親 ID (如果為 None 則不更新)
            mom_id: 母親 ID (如果為 None 則不更新)
            
        Returns:
            bool: 更新是否成功
        """
        if dad_id is None and mom_id is None:
            return False
            
        try:
            update_parts = []
            params = []
            
            if dad_id is not None:
                update_parts.append("dad_id = ?")
                params.append(dad_id)
            
            if mom_id is not None:
                update_parts.append("mom_id = ?")
                params.append(mom_id)
            
            params.append(member_id)
            
            query = f"""
            UPDATE {dbm.db_tables['members']} 
            SET {', '.join(update_parts)}
            WHERE id = ?
            """
            
            self.cursor.execute(query, params)
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"成功更新成員 ID {member_id} 的父母信息")
                return True
            else:
                logger.warning(f"未找到成員 ID {member_id} 或無需更新")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"更新成員 {member_id} 的父母信息時出錯: {e}")
            self.conn.rollback()
            return False
    
    def process_all_members(self):
        """處理所有需要更新父母關係的成員"""
        try:
            rcds = self.get_members_with_parents()
            total = len(rcds)
            updated = 0
            skipped = 0
            
            logger.info(f"開始處理 {total} 個成員的父母關係更新...")
            
            for i, rcd in enumerate(rcds, 1):
                gen_order = rcd.get('Order')
                born = rcd.get('Born')
                name = rcd.get('Name')
                father_name = rcd.get('Dad')
                mother_name = rcd.get('Mom')
                
                logger.info(f"處理進度: {i}/{total} - 成員: {name} (世代: {gen_order}, 出生: {born})")
                
                # 查找當前成員的 ID
                member_id = self.find_member_id(name, born, gen_order)
                if not member_id:
                    logger.warning(f"未找到成員: 姓名={name}, 出生日期={born}, 世代順序={gen_order}")
                    skipped += 1
                    continue
                
                # 查找父親 ID
                dad_id = None
                if father_name:
                    # 父親的世代順序應該是當前成員的世代順序 - 1
                    dad_gen_order = gen_order - 1 if gen_order is not None else None
                    dad_id = self.find_member_id(father_name, None, dad_gen_order)
                    if not dad_id:
                        logger.warning(f"未找到父親: {father_name} (成員: {name})")
                
                # 查找母親 ID
                mom_id = None
                if mother_name:
                    # 母親的世代順序應該是當前成員的世代順序 - 1
                    mom_gen_order = gen_order - 1 if gen_order is not None else None
                    mom_id = self.find_member_id(mother_name, None, mom_gen_order)
                    if not mom_id:
                        logger.warning(f"未找到母親: {mother_name} (成員: {name})")
                
                # 更新成員的父母信息
                if dad_id is not None or mom_id is not None:
                    success = self.update_member_parents(member_id, dad_id, mom_id)
                    if success:
                        updated += 1
                    else:
                        skipped += 1
                else:
                    logger.warning(f"成員 {name} 的父母均未找到，跳過更新")
                    skipped += 1
            
            logger.info(f"處理完成！共處理 {total} 個成員，成功更新 {updated} 個，跳過 {skipped} 個。")
            return updated, skipped
            
        except Exception as e:
            logger.error(f"處理過程中出錯: {e}", exc_info=True)
            return 0, 0

def main():
    """主函數"""
    try:
        with MemberParentUpdater() as updater:
            updated, skipped = updater.process_all_members()
            print(f"\n處理完成！")
            print(f"總共處理成員: {updated + skipped}")
            print(f"成功更新: {updated}")
            print(f"跳過: {skipped}")
            
            # show the total number of records in the `members` table
            logger.info(f"Total records in members table: {dbm.get_total_records(dbm.db_tables['members'])}")
            print(f"Total records in members table: {dbm.get_total_records(dbm.db_tables['members'])}")
            print(f"\n詳細日誌已保存到 {LOG_FILE} 文件")
            return 0 if updated + skipped == 0 else 1
    except Exception as e:
        logger.error(f"程序執行出錯: {e}", exc_info=True)
        print(f"\n程序執行出錯: {e}")
        print(f"請查看 {LOG_FILE} 文件獲取詳細錯誤信息")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
