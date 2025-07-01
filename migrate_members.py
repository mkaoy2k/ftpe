"""
Migration script for importing member data from 
pre-2.5 release me.csv format to SQLite database.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import db_utils as dbm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_FIELDS = ['Name', 'Sex', 'Born', 'Order']
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
    member_data = {
        'name': row['Name'].strip(),
        'sex': row['Sex'].strip(),
        'born': row['Born'].strip(),
        'family_id': row.get('FamilyID', '').strip(),
        'alias': row.get('Aka', '').strip(),
        'email': row.get('Email', '').strip(),
        'url': row.get('Href', '').strip(),
        'died': row.get('Died', '').strip() or None,
        'gen_order': int(row['Order']) if row.get('Order', '').strip().isdigit() else 0
    }
    
    # Remove empty values
    return {k: v for k, v in member_data.items() if v is not None and v != ''}

def import_csv_to_db(csv_file_path: Path) -> Tuple[int, int]:
    """
    Import member data from CSV file to database.
    
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
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    member_data = process_member_row(row)
                    member_id = dbm.add_member(member_data)
                    
                    if member_id:
                        imported_count += 1
                        logger.info(f"Added member: {member_data['name']} (ID: {member_id})")
                    else:
                        error_count += 1
                        logger.warning(f"Failed to add member: {member_data['name']}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing row {row_num}: {str(e)}", exc_info=True)
            
            return imported_count, error_count
            
    except Exception as e:
        raise CSVImportError(f"Error during CSV import: {str(e)}")

def migrate_members() -> bool:
    """
    Main function to handle the CSV import process.
    
    Returns:
        bool: True if import was successful (no errors), False otherwise
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
        logger.info(f"  - Successfully imported: {imported} members")
        logger.info(f"  - Failed to import: {errors} members")
        
        return errors == 0
            
    except CSVImportError as e:
        logger.error(f"Import error: {str(e)}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = migrate_members()
    sys.exit(0 if success else 1)
