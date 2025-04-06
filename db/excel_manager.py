"""
ExcelDatabase class for managing Excel spreadsheet data in MongoDB.
"""

import logging
from pathlib import Path
from typing import Optional, List, Union, Dict, Any

from .database import connect_db, disconnect_db
from .models import Spreadsheet
from parsers.excel_parser import ExcelParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelDatabase:
    """
    A class to manage Excel spreadsheet data in MongoDB.
    Provides methods for loading spreadsheets and querying cell data.
    """
    
    def __init__(self, spreadsheet_path: Union[str, Path], auto_connect: bool = True):
        """
        Initialize the ExcelDatabase with a spreadsheet path.
        
        Args:
            spreadsheet_path: Path to the Excel spreadsheet
            auto_connect: Whether to automatically connect to the database (default: True)
        """
        self.spreadsheet_path = Path(spreadsheet_path)
        self.spreadsheet = None
        self.parser = None
        
        if auto_connect:
            self.connect()
    
    def connect(self) -> None:
        """Connect to the MongoDB database."""
        connect_db()
    
    def disconnect(self) -> None:
        """Disconnect from the MongoDB database."""
        disconnect_db()
    
    def load_spreadsheet(self) -> bool:
        """
        Load the spreadsheet into the database using ExcelParser.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.spreadsheet_path.exists():
            logger.error(f"Spreadsheet not found: {self.spreadsheet_path}")
            return False
        
        try:
            logger.info(f"Parsing spreadsheet: {self.spreadsheet_path}")
            self.parser = ExcelParser(str(self.spreadsheet_path))
            self.spreadsheet = self.parser.parse()
            
            # Display information about the parsed spreadsheet
            logger.info(f"Parsed spreadsheet: {self.spreadsheet.name}")
            logger.info(f"Number of cells: {len(self.spreadsheet.cells)}")
            logger.info(f"Sheets: {', '.join(self.spreadsheet.sheet_names)}")
            return True
        except Exception as e:
            logger.error(f"Error processing {self.spreadsheet_path.name}: {str(e)}")
            return False
    
    def delete_spreadsheet(self, name: Optional[str] = None, filename: Optional[str] = None) -> bool:
        """
        Delete a spreadsheet and all its cells from the database.
        
        Args:
            name: The name of the spreadsheet to delete
            filename: The original filename of the spreadsheet to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not (name or filename):
            logger.error("Either name or filename must be specified for deletion")
            return False
            
        try:
            # Find the spreadsheet to delete
            query = {}
            if name:
                query['name'] = name
            if filename:
                query['original_filename'] = filename
                
            spreadsheet = Spreadsheet.objects(**query).first()
            
            if not spreadsheet:
                logger.error(f"Spreadsheet not found with query: {query}")
                return False
                
            # Get the spreadsheet ID before deletion for logging
            spreadsheet_id = str(spreadsheet.id)
            spreadsheet_name = spreadsheet.name
            
            # Count cells before deletion for logging
            cell_count = len(spreadsheet.cells)
            
            # Delete the spreadsheet which will delete all its reference cells due to
            # the cascade delete behavior defined in the model
            spreadsheet.delete()
            
            logger.info(f"Deleted spreadsheet '{spreadsheet_name}' (ID: {spreadsheet_id}) with {cell_count} cells")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting spreadsheet: {str(e)}")
            return False
    
    def reparse_spreadsheet(self, name: Optional[str] = None, filename: Optional[str] = None) -> bool:
        """
        Delete an existing spreadsheet from the database and reparse it.
        
        Args:
            name: The name of the spreadsheet to reparse
            filename: The original filename of the spreadsheet to reparse
            
        Returns:
            bool: True if reparsing was successful, False otherwise
        """
        # Delete the existing spreadsheet if it exists
        if name or filename:
            deleted = self.delete_spreadsheet(name=name, filename=filename)
            if not deleted:
                logger.warning("No existing spreadsheet was deleted. Continuing with parsing.")
        
        # Load the spreadsheet
        return self.load_spreadsheet()
    
    def get_spreadsheet_data(self, name: Optional[str] = None, filename: Optional[str] = None, 
                      limit: int = 10, as_dict: bool = False) -> Union[List[Union[Spreadsheet, Dict[str, Any]]], 
                                                                     Optional[Union[Spreadsheet, Dict[str, Any]]]]:
        """
        Fetch Spreadsheet objects from the database.
        
        Args:
            name: Filter by spreadsheet name
            filename: Filter by original filename
            limit: Maximum number of results to return (when returning multiple)
            as_dict: Whether to return results as dictionaries instead of Spreadsheet objects
            
        Returns:
            - If name or filename is specified and as_dict=False: A single Spreadsheet object or None
            - If name or filename is specified and as_dict=True: A dictionary or None
            - If neither name nor filename is specified and as_dict=False: A list of Spreadsheet objects
            - If neither name nor filename is specified and as_dict=True: A list of dictionaries
        """
        try:
            # Single spreadsheet lookup
            if name or filename:
                query = {}
                if name:
                    query['name'] = name
                if filename:
                    query['original_filename'] = filename
                
                spreadsheet = Spreadsheet.objects(**query).first()
                
                if not spreadsheet:
                    logger.error(f"Spreadsheet not found with query: {query}")
                    return None
                
                if as_dict:
                    return self._spreadsheet_to_dict(spreadsheet)
                return spreadsheet
                
            # Multiple spreadsheets lookup
            else:
                spreadsheets = Spreadsheet.objects.limit(limit)
                
                if not spreadsheets:
                    logger.info("No spreadsheets found in database.")
                    return []
                
                if as_dict:
                    return [self._spreadsheet_to_dict(s) for s in spreadsheets]
                return list(spreadsheets)
                
        except Exception as e:
            logger.error(f"Error fetching spreadsheet(s): {str(e)}")
            return None if (name or filename) else []
    
    def _spreadsheet_to_dict(self, spreadsheet: Spreadsheet) -> Dict[str, Any]:
        """
        Convert a Spreadsheet object to a dictionary.
        
        Args:
            spreadsheet: The Spreadsheet object to convert
            
        Returns:
            dict: Dictionary representation of the spreadsheet
        """
        # Create a list of cell references with sheet_name
        cell_references = []
        for cell in spreadsheet.cells:
            cell_references.append({
                "cell_ref": cell.cell_reference,
                "sheet_name": cell.sheet_name
            })
            
        return {
            'id': str(spreadsheet.id),
            'name': spreadsheet.name,
            'original_filename': spreadsheet.original_filename,
            'file_path': spreadsheet.file_path,
            'sheet_names': spreadsheet.sheet_names,
            'active_sheet': spreadsheet.active_sheet,
            'cell_count': len(spreadsheet.cells),
            'cell_references': cell_references,
            'metadata': spreadsheet.metadata,
            'created_at': spreadsheet.created_at,
            'updated_at': spreadsheet.updated_at
        }
    
    def get_cell_data(self, cell_reference: str, sheet_name: Optional[str] = None) -> Optional[dict]:
        """
        Fetch data for a specific cell.
        
        Args:
            cell_reference: Excel-style cell reference (e.g., "A1", "B2")
            sheet_name: Name of the sheet (defaults to active sheet if None)
        
        Returns:
            dict: Dictionary containing cell data if found, None otherwise
        """
        if not self.spreadsheet:
            logger.error("No spreadsheet loaded. Call load_spreadsheet() first.")
            return None
            
        try:
            # If sheet_name not provided, use active sheet
            if sheet_name is None:
                sheet_name = self.spreadsheet.active_sheet
            
            # Verify that the sheet exists in the spreadsheet
            if sheet_name not in self.spreadsheet.sheet_names:
                logger.error(f"Sheet '{sheet_name}' not found in spreadsheet")
                return None
            
            # Find the cell
            cell = self.spreadsheet.get_cell_by_reference(cell_reference, sheet_name)
            
            if not cell:
                sheet_info = f" in sheet '{sheet_name}'" if sheet_name else ""
                logger.error(f"Cell '{cell_reference}'{sheet_info} not found")
                return None
            
            # Return cell data as a dictionary
            return {
                'row': cell.row,
                'column': cell.column,
                'sheet': cell.sheet_name or sheet_name,
                'value': cell.value,
                'formatted_value': cell.formatted_value,
                'alias': cell.alias,
                'value_list': cell.value_list,
                'formula': cell.formula,
                'data_type': cell.data_type,
                'cell_type': cell.cell_type,
                'precedent_cells': cell.precedent_cells,
                'dependent_cells': cell.dependent_cells,
                'metadata': cell.metadata
            }
            
        except Exception as e:
            logger.error(f"Error fetching cell data: {str(e)}")
            return None
    
    def get_sheet_data(self, sheet_name: Optional[str] = None) -> Optional[dict]:
        """
        Get all data from a specific sheet.
        
        Args:
            sheet_name: Name of the sheet (defaults to active sheet if None)
        
        Returns:
            dict: Dictionary containing all cells in the sheet with cell references as keys,
                  or None if the sheet doesn't exist or an error occurs
        """
        if not self.spreadsheet:
            logger.error("No spreadsheet loaded. Call load_spreadsheet() first.")
            return None
            
        try:
            # If sheet_name not provided, use active sheet
            if sheet_name is None:
                sheet_name = self.spreadsheet.active_sheet
            
            # Check if sheet exists
            if sheet_name not in self.spreadsheet.sheet_names:
                logger.error(f"Sheet '{sheet_name}' not found in spreadsheet")
                return None
                
            # Get all cells for the given sheet
            sheet_cells = {}
            for cell in self.spreadsheet.cells:
                if cell.sheet_name == sheet_name:
                    cell_reference = f"{cell.column}{cell.row}"
                    sheet_cells[cell_reference] = {
                        'row': cell.row,
                        'column': cell.column,
                        'value': cell.value,
                        'formatted_value': cell.formatted_value,
                        'formula': cell.formula,
                        'data_type': cell.data_type,
                        'cell_type': cell.cell_type
                    }
            
            return {
                'name': sheet_name,
                'cells': sheet_cells
            }
            
        except Exception as e:
            logger.error(f"Error fetching sheet data: {str(e)}")
            return None
    
    def get_sheet_names(self) -> List[str]:
        """
        Get the list of sheet names in the spreadsheet.
        
        Returns:
            List[str]: List of sheet names
        """
        if not self.spreadsheet:
            logger.error("No spreadsheet loaded. Call load_spreadsheet() first.")
            return []
        return self.spreadsheet.sheet_names
    
    def get_active_sheet(self) -> str:
        """
        Get the name of the active sheet.
        
        Returns:
            str: Name of the active sheet
        """
        if not self.spreadsheet:
            logger.error("No spreadsheet loaded. Call load_spreadsheet() first.")
            return ""
        return self.spreadsheet.active_sheet
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect() 