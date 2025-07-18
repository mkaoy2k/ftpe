"""
Migration script for migrating member data from the `mirrors` table to the `members` table.
This script ensures data integrity by using (name, born, gen_order) as a unique key.

Field mapping from mirrors to members table:
- name -> name (required)
- aka -> alias
- born -> born (required)
- died -> died
- gen_order -> gen_order (required)
- href -> url
"""
import logging
import sys
from typing import Dict, Any, List, Tuple
import db_utils as dbm
from datetime import datetime
import sqlite3
from pathlib import Path

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

class MigrationError(Exception):
    """Custom exception for migration errors."""
    pass

def get_mirrors_data() -> List[Dict[str, Any]]:
    """
    Fetch all records from the mirrors table with only the required fields.
    
    Returns:
        List of dictionaries containing mirror records with fields:
        - Name, Aka, Born, Died, Order, Href
    """
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT Name, Aka, Born, Died, "Order", Href 
                FROM {dbm.db_tables['mirrors']}
                WHERE Name IS NOT NULL and Name is not '?'
            """)
            columns = ['Name', 'Aka', 'Born', 'Died', 'Order', 'Href']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error fetching mirrors data: {str(e)}")
        raise MigrationError(f"Failed to fetch mirrors data: {str(e)}")

def map_mirror_to_member(mirror_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map fields from mirrors table to members table format.
    Only processes the 6 specified fields.
    
    Args:
        mirror_data: Dictionary containing data from mirrors table
        
    Returns:
        Dictionary with mapped member data
    """
    # Required fields with defaults
    # Get born date, default to '0000-01-01' if zero or missing
    born = mirror_data.get('Born', 0)
    if born == 0 or born == '0' or not born:
        born = '0000-01-01'
    died = mirror_data.get('Died', 0)
    if died == 0 or died == '0' or not died:
        died = '0000-01-01'
    alias = mirror_data.get('Aka', '')
    if not alias:
        alias = ''
    href = mirror_data.get('Href', '')
    if not href:
        href = ''
    
    # field mapping from mirrors to members
    member_data = {
        'name': mirror_data.get('Name', '').strip(),
        'born': born,
        'gen_order': int(mirror_data.get('Order', 0)),
        'alias': alias,
        'died': died,
        'url': href
    }
    
    return member_data

def migrate_members() -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Migrate data from mirrors table to members table.
    
    Returns:
        Tuple of (migrated_count, error_count, error_details)
        error_details is a list of dictionaries containing error information
    """
    migrated_count = 0
    error_count = 0
    error_details = []
    
    try:
        # Get all records from mirrors table
        logger.info("Fetching data from mirrors table...")
        mirrors_data = get_mirrors_data()
        total_records = len(mirrors_data)
        logger.info(f"Found {total_records} records in mirrors table")
        
        if total_records == 0:
            logger.warning("No records found in mirrors table")
            return 0, 0, []
        
        # Process each record
        for i, mirror_record in enumerate(mirrors_data, 1):
            try:
                logger.info(f"Processing record {i}/{total_records}...\t{mirror_record.get('Name', 'Unknown')}\t{mirror_record.get('Born', 'Unknown')}\t{mirror_record.get('Order', 'Unknown')}")
                # Map data to member format
                member_data = map_mirror_to_member(mirror_record)
                
                # Check if all required fields exist in the dictionary
                if not all(field in member_data for field in [
                    'name', 'born', 'gen_order',
                    'alias', 'died', 'url']):
                    error_msg = f"Missing required fields in record {i}: {member_data}"
                    logger.warning(error_msg)
                    error_details.append({
                        'record': mirror_record,
                        'error': 'Missing required fields',
                        'details': error_msg
                    })
                    error_count += 1
                    continue
                
                # Add or update member in database
                member_id = dbm.add_or_update_member(member_data, 
                                                     update=True)
                
                if member_id:
                    migrated_count += 1
                    logger.info(f"Processed {i}/{total_records} records.\t{member_data.get('name')}\t{member_data.get('born')}\t{member_data.get('gen_order')}")
                else:
                    error_msg = f"Failed to add/update member: {member_data.get('name')}\t{member_data.get('born')}\t{member_data.get('gen_order')}"
                    logger.warning(error_msg)
                    error_details.append({
                        'record': mirror_record,
                        'error': 'Database operation failed',
                        'details': error_msg
                    })
                    error_count += 1
            
            except Exception as e:
                error_msg = f"Error processing record {i}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                error_details.append({
                    'record': mirror_record,
                    'error': str(type(e).__name__),
                    'details': error_msg
                })
                error_count += 1
        
        return migrated_count, error_count, error_details
    
    except Exception as e:
        error_msg = f"Migration failed: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        raise MigrationError(error_msg) from e

def main() -> int:
    """Main function to run the migration."""
    logger.info("Starting migration from mirrors to members table...")
    print("Starting migration from mirrors to members table...")
    try:
        # Initialize database
        dbm.init_db()
        
        # Run migration
        start_time = datetime.now()
        migrated, errors, error_details = migrate_members()
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log summary
        logger.info("\n=== Migration Summary ===")
        logger.info(f"Total records processed: {migrated + errors}")
        logger.info(f"Successfully migrated: {migrated}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        # Print the summary to the console
        print("\n=== Migration Summary ===")
        print(f"Total records processed: {migrated + errors}")
        print(f"Successfully migrated: {migrated}")
        print(f"Errors: {errors}")
        print(f"Duration: {duration:.2f} seconds")
         
        # Log errors if any
        if errors > 0:
            print(f"check error details in {LOG_FILE}")
            logger.warning("\n=== Error Details ===")
            for i, error in enumerate(error_details[:10], 1):  # Show first 10 errors
                logger.warning(f"{i}. {error['error']}: {error['details']}")
            if len(error_details) > 10:
                logger.warning(f"... and {len(error_details) - 10} more errors")
        
        # show the total number of records in the `members` table
        logger.info(f"Total records in members table: {dbm.get_total_records(dbm.db_tables['members'])}")
        print(f"Total records in members table: {dbm.get_total_records(dbm.db_tables['members'])}")
        print(f"\nMigration summary details saved to {LOG_FILE} file")
        return 0 if errors == 0 else 1
    
    except Exception as e:
        logger.critical(f"Fatal error during migration: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
