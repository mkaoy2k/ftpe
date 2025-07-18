"""
Migration script for importing members from 
pre-2.x release in me.csv format to SQLite mirrors table.
Field names in mirrors table (see db_tils.py):
    name TEXT NOT NULL,
    aka TEXT,
    sex INTEGER,
    born DATE,
    died DATE,
    dad TEXT,
    mom TEXT,
    relation INTEGER DEFAULT 0,
    spouse TEXT,
    married DATE,
    gen_order INTEGER DEFAULT 0,
    href TEXT,
    status INTEGER DEFAULT 0
"""
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
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
REQUIRED_FIELDS = ['Name', 'Aka', 'Sex', 'Born', 'Died',
                   'Dad', 'Mom', 'Relation', 
                   'Spouse', 'Married',
                   'Order', 'Href', 'Status']
DEFAULT_DATA_DIR = Path('data')
DEFAULT_CSV_FILE = 'me.csv'

class CSVImportError(Exception):
    """Custom exception for CSV import related errors."""
    pass

def validate_csv_file(file_path: Path) -> Tuple[bool, str]:
    """
    Validate if the CSV file exists and has the required fields.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return False, error_msg
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            
            # Check for missing required fields
            missing_fields = [f for f in REQUIRED_FIELDS if f not in fieldnames]
            if missing_fields:
                return False, f"Error: Missing required fields: {', '.join(missing_fields)}"
            return True, ""
            
    except Exception as e:
        return False, f"Error reading CSV file: {str(e)}"

def process_member_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Process a single row of member data from CSV.
    
    Args:
        row: Dictionary containing CSV row data
        
    Returns:
        Dictionary with processed member data
    """
        # Required fields with defaults
    # Get born date, default to '0000-01-01' if zero or missing
    born = row.get('Born', 0)
    if born == 0 or born == '0' or not born:
        born = '0000-01-01'
    died = row.get('Died', 0)
    if died == 0 or died == '0' or not died:
        died = '0000-01-01'
    married = row.get('Married', 0)
    if married == 0 or married == '0' or not married:
        married = '0000-01-01'
    
    member_data = {
        'Name': row['Name'].strip(),
        'Aka': row['Aka'].strip(),
        'Sex': row['Sex'].strip(),
        'Born': born,
        'Died': died,
        'Dad': row.get('Dad', '').strip(),
        'Mom': row.get('Mom', '').strip(),
        'Relation': int(row.get('Relation', '0').strip()),
        'Spouse': row.get('Spouse', '').strip(),
        'Married': married,
        'Order': int(row.get('Order', '0').strip()),
        'Href': row.get('Href', '').strip(),
        'Status': int(row.get('Status', '0').strip())
    }
    
    # Remove empty values
    return {k: v for k, v in member_data.items() if v is not None and v != ''}

def import_csv_to_db(csv_file_path: Path) -> Tuple[int, int]:
    """
    Import member data from CSV file to names table.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        Tuple of (imported_count, error_count)
        
    Raises:
        CSVImportError: If there's an error during import
    """
    # Validate the CSV file first
    is_valid, error_msg = validate_csv_file(csv_file_path)
    if not is_valid:
        raise CSVImportError(error_msg)
    
    imported_count = 0
    error_count = 0
    
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Process the row data
                        member_data = process_member_row(row)
                        
                        # Insert into  table
                        cursor.execute(f"""
                            INSERT INTO {dbm.db_tables['mirrors']} (
                                Name, Aka, Sex, Born, Died, 
                                Dad, Mom, Relation,
                                Spouse, Married, 
                                "Order", Href, Status
                            ) VALUES (?, ?, ?, ?, ?,
                            ?, ?, ?, 
                            ?, ?, 
                            ?, ?, ?)
                        """, (
                            member_data.get('Name'),
                            member_data.get('Aka'),
                            member_data.get('Sex'),
                            member_data.get('Born'),
                            member_data.get('Died'),
                            member_data.get('Dad'),
                            member_data.get('Mom'),
                            member_data.get('Relation'),
                            member_data.get('Spouse'),
                            member_data.get('Married'),
                            member_data.get('Order'),
                            member_data.get('Href'),
                            member_data.get('Status')
                        ))
                        
                        imported_count += 1
                        logger.info(f"Added name: {member_data.get('Name', 'Unknown')}\t{member_data.get('Born', 'Unknown')}\t{member_data.get('Order', 'Unknown')}")    
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing row {row_num}: {str(e)}", exc_info=True)
                
                # Commit the transaction
                conn.commit()
                
            return imported_count, error_count
            
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        raise CSVImportError(f"Error during CSV import: {str(e)}")

def migrate_members() -> bool:
    """
    Main function to handle the CSV import process.
    
    Returns:
        bool: True if import was successful (no errors), 
        False otherwise
    """
    try:
        # Set up file paths
        csv_file = DEFAULT_DATA_DIR / DEFAULT_CSV_FILE
        
        # Check if file exists
        if not csv_file.exists():
            logger.error(f"File not found: {csv_file}")
            logger.error(f"Please make sure {DEFAULT_CSV_FILE} exists in the {DEFAULT_DATA_DIR} directory")
            return False
        
        # Import data
        logger.info(f"Starting import from {csv_file}...")
        imported, errors = import_csv_to_db(csv_file)
        
        # Log summary
        logger.info("\nImport completed!")
        print("\nImport completed!")
        logger.info(f"  - Successfully imported: {imported} names")
        print(f"  - Successfully imported: {imported} names")
        logger.info(f"  - Failed to import: {errors} names")
        print(f"  - Failed to import: {errors} names")
        logger.info(f"The number of records in the `mirrors` table: {dbm.get_total_records(dbm.db_tables['mirrors'])}")
        print(f"The number of records in the `mirrors` table: {dbm.get_total_records(dbm.db_tables['mirrors'])}")
        print(f"\nImport summary details saved to {LOG_FILE} file")
        
        return errors == 0
            
    except CSVImportError as e:
        logger.error(f"Import error: {str(e)}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    dbm.init_db()
    success = migrate_members()
    sys.exit(0 if success else 1)
