"""This script updates the 'sex' field in the 'members' table 
based on the 'sex' field in the 'mirrors' table.
converting
dbm.Member_Sex[male] -> M
dbm.Member_Sex[female] -> F
dbm.Member_Sex[inlaw-male] -> M
dbm.Member_Sex[inlaw-female] -> F
"""
import logging
import sys
from typing import Dict, Any, List, Tuple, Optional
import db_utils as dbm
from datetime import datetime
import sqlite3
from pathlib import Path
import db_utils as dbm

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

# Constants
REQUIRED_FIELDS = ['Name', 'Sex', 'Born', 'Order']

def convert_sex(mirrors_sex: int) -> Optional[str]:
    """
    Convert sex value from mirrors table to members table format.
    
    Args:
        mirrors_sex: The sex value from the mirrors table
        
    Returns:
        str: 'M' for male, 'F' for female, or None if invalid
    """
    if mirrors_sex == dbm.Member_Sex['male'] or mirrors_sex == dbm.Member_Sex['inlaw-male']:
        return 'M'
    elif mirrors_sex == dbm.Member_Sex['female'] or mirrors_sex == dbm.Member_Sex['inlaw-female']:
        return 'F'
    return None

def get_mirrors_records() -> List[Dict[str, Any]]:
    """
    Get all records from the mirrors table with non-null Sex field.
    
    Returns:
        List of dictionaries containing mirror records
    """
    try:
        with dbm.get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = f"""
                SELECT "Order", Born, Name, Sex
                FROM {dbm.db_tables['mirrors']}
                WHERE Sex IS NOT NULL
                AND Name IS NOT NULL
                AND Born IS NOT NULL
                AND "Order" IS NOT NULL
            """
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
            
    except sqlite3.Error as e:
        logger.error(f"Database error fetching mirrors records: {str(e)}")
        raise

def find_matching_member(conn: sqlite3.Connection, name: str, born: str, order: int) -> Optional[Dict[str, Any]]:
    """
    Find a member in the members table that matches the given criteria.
    
    Args:
        conn: Database connection
        name: Member name
        born: Birth date
        order: Generation order
        
    Returns:
        Dictionary with member data if exactly one match is found, None otherwise
    """
    try:
        cursor = conn.cursor()
        query = f"""
            SELECT id, name, born, gen_order, sex
            FROM {dbm.db_tables['members']}
            WHERE name = ? 
            AND born = ? 
            AND gen_order = ?
        """
        cursor.execute(query, (name, born, order))
        results = cursor.fetchall()
        
        if len(results) == 1:
            return dict(results[0])
        elif len(results) > 1:
            logger.warning(f"Multiple matches found for {name} (Born: {born}, Order: {order})")
        else:
            logger.warning(f"No match found for {name} (Born: {born}, Order: {order})")
            
    except sqlite3.Error as e:
        logger.error(f"Database error finding member {name}: {str(e)}")
        
    return None

def update_member_sex(conn: sqlite3.Connection, member_id: int, new_sex: str) -> bool:
    """
    Update the sex field for a member.
    
    Args:
        conn: Database connection
        member_id: ID of the member to update
        new_sex: New sex value ('M' or 'F')
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        query = f"""
            UPDATE {dbm.db_tables['members']}
            SET sex = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        cursor.execute(query, (new_sex, member_id))
        conn.commit()
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error updating member {member_id}: {str(e)}")
        return False

def main():
    """Main function to update member sex fields."""
    logger.info("Starting member sex update process")
    
    try:
        # Get all relevant records from mirrors table
        mirrors_records = get_mirrors_records()
        logger.info(f"Found {len(mirrors_records)} records in mirrors table with non-null Sex field")
        
        if not mirrors_records:
            logger.warning("No records found in mirrors table with non-null Sex field")
            return
        
        # Process each record
        updated = 0
        skipped = 0
        errors = 0
        
        with dbm.get_db_connection() as conn:
            for record in mirrors_records:
                try:
                    # Convert sex value
                    new_sex = convert_sex(record['Sex'])
                    if not new_sex:
                        logger.warning(f"Skipping record with invalid sex value: {record}")
                        skipped += 1
                        continue
                    
                    # Find matching member
                    member = find_matching_member(
                        conn, 
                        record['Name'], 
                        record['Born'], 
                        record['Order']
                    )
                    
                    if not member:
                        skipped += 1
                        continue
                    
                    # Skip if sex is already correct
                    if member.get('sex') == new_sex:
                        logger.debug(f"Sex already correct for {member['name']} (ID: {member['id']})")
                        skipped += 1
                        continue
                    
                    # Update member sex
                    if update_member_sex(conn, member['id'], new_sex):
                        logger.info(
                            f"Updated {member['name']} (ID: {member['id']}) "
                            f"sex from '{member.get('sex')}' to '{new_sex}'"
                        )
                        updated += 1
                    else:
                        logger.warning(f"Failed to update {member['name']} (ID: {member['id']})")
                        errors += 1
                        
                except Exception as e:
                    logger.error(f"Error processing record {record}: {str(e)}")
                    errors += 1
        
        # Log summary
        logger.info("\nUpdate Summary:")
        logger.info(f"  Total records processed: {len(mirrors_records)}")
        logger.info(f"  Successfully updated: {updated}")
        logger.info(f"  Skipped: {skipped}")
        logger.info(f"  Errors: {errors}")
        
        print("\nUpdate Summary:")
        print(f"  Total records processed: {len(mirrors_records)}")
        print(f"  Successfully updated: {updated}")
        print(f"  Skipped: {skipped}")
        print(f"  Errors: {errors}")
        
        # show the total number of records in the `members` table
        logger.info(f"Total records in members table: {dbm.get_total_records(dbm.db_tables['members'])}")
        print(f"Total records in members table: {dbm.get_total_records(dbm.db_tables['members'])}")
        print(f"\nMigration summary details saved to {LOG_FILE} file")
        return 0 if errors == 0 else 1
    
    except Exception as e:
        logger.error(f"Fatal error in main process: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
