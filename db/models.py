"""
Database models for the Excel to Python LLM agent project.

This module defines the MongoDB document models using MongoEngine ODM.
"""

from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from mongoengine import (
    Document, 
    EmbeddedDocument,
    StringField,
    IntField,
    DateTimeField,
    DictField,
    ListField,
    EmbeddedDocumentListField,
    BooleanField
)


class Cell(EmbeddedDocument):
    """
    Embedded document representing a cell in a spreadsheet.
    
    Attributes:
        row: The row index of the cell (0-indexed).
        column: The column index of the cell (0-indexed).
        cell_reference: The Excel-style cell reference (e.g., "A1", "B2", "AA10").
        value: The raw value of the cell.
        formatted_value: The formatted display value of the cell.
        alias: User-defined name/alias for the cell.
        value_list: List of values when cell contains multiple values.
        formula: The formula in the cell, if any.
        formula_inputs: List of cell references that are inputs to this cell's formula.
        sheet_name: The name of the sheet this cell belongs to.
        data_type: The data type of the cell (string, number, date, etc.).
        cell_type: The type of cell (value, list, formula, etc.).
        precedent_cells: List of dictionaries containing cell references, sheet names, and workbook names that this cell depends on.
        dependent_cells: List of dictionaries containing cell references, sheet names, and workbook names that depend on this cell.
        metadata: Additional metadata for the cell.
        created_at: When the cell was first created.
        updated_at: When the cell value was last updated.
        accessed_at: When the cell was last accessed by the LLM agent.
    """
    row = IntField(required=True)
    column = IntField(required=True)
    cell_reference = StringField(required=True)
    value = DictField(default={})  # Flexible field to store different types
    formatted_value = StringField()
    alias = StringField()  # User-defined name/alias for the cell
    value_list = ListField(default=[])  # List of values when cell contains multiple values
    formula = StringField()
    formula_inputs = ListField(StringField(), default=[])  # List of cell references that are inputs to this cell's formula
    sheet_name = StringField(required=True)  # Name of the sheet this cell belongs to
    data_type = StringField()
    cell_type = StringField(choices=["value", "valuelist", "formula"])  # Type of cell content
    precedent_cells = ListField(DictField(), default=[])  # List of dicts with cell_ref, sheet_name, workbook_name
    dependent_cells = ListField(DictField(), default=[])  # List of dicts with cell_ref, sheet_name, workbook_name
    metadata = DictField(default={})
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))
    accessed_at = DateTimeField(default=lambda: datetime.now(UTC))
    
    def __str__(self) -> str:
        return f"{self.sheet_name}!{self.cell_reference}: {self.formatted_value or self.value}"
        
    def update_access_time(self):
        """Update the accessed_at timestamp to the current time."""
        self.accessed_at = datetime.now(UTC)
        
    def update_value(self, new_value):
        """
        Update the cell value and update the updated_at timestamp.
        
        Args:
            new_value: The new value to set for the cell.
        """
        self.value = new_value
        self.updated_at = datetime.now(UTC)
        
    def add_precedent(self, cell_ref, sheet_name=None, workbook_name=None):
        """
        Add a precedent cell to this cell's precedent list.
        
        Args:
            cell_ref: The cell reference (e.g., "A1", "B2").
            sheet_name: The name of the sheet containing the precedent cell.
            workbook_name: The name of the workbook containing the precedent cell.
        """
        precedent = {
            "cell_ref": cell_ref,
            "sheet_name": sheet_name,
            "workbook_name": workbook_name
        }
        if precedent not in self.precedent_cells:
            self.precedent_cells.append(precedent)
            
    def add_dependent(self, cell_ref, sheet_name=None, workbook_name=None):
        """
        Add a dependent cell to this cell's dependent list.
        
        Args:
            cell_ref: The cell reference (e.g., "A1", "B2").
            sheet_name: The name of the sheet containing the dependent cell.
            workbook_name: The name of the workbook containing the dependent cell.
        """
        dependent = {
            "cell_ref": cell_ref,
            "sheet_name": sheet_name,
            "workbook_name": workbook_name
        }
        if dependent not in self.dependent_cells:
            self.dependent_cells.append(dependent)

class Spreadsheet(Document):
    """
    Document representing an Excel spreadsheet.
    
    Attributes:
        name: The name of the spreadsheet.
        original_filename: The original filename of the uploaded spreadsheet.
        file_path: Path to the stored file, if applicable.
        sheet_names: List of sheet names in the spreadsheet.
        active_sheet: The name of the active sheet.
        cells: List of Cell embedded documents.
        metadata: Additional metadata for the spreadsheet.
        created_at: When the document was created.
        updated_at: When the document was last updated.
    """
    name = StringField(required=True)
    original_filename = StringField(required=True)
    file_path = StringField()
    sheet_names = ListField(StringField())
    active_sheet = StringField()
    cells = EmbeddedDocumentListField(Cell)
    metadata = DictField(default={})
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))
    
    meta = {
        'collection': 'spreadsheets',
        'indexes': [
            'name',
            'original_filename',
            'created_at'
        ]
    }
    
    def save(self, *args, **kwargs):
        """Override save method to update the updated_at field."""
        self.updated_at = datetime.now(UTC)
        return super(Spreadsheet, self).save(*args, **kwargs)
    
    def get_cell(self, row: int, column: int, sheet_name: str = None) -> Optional[Cell]:
        """
        Get a cell by its row and column indices.
        
        Args:
            row: The row index.
            column: The column index.
            sheet_name: The name of the sheet (defaults to active_sheet if None).
            
        Returns:
            The Cell object if found, None otherwise.
        """
        if sheet_name is None:
            sheet_name = self.active_sheet
            
        for cell in self.cells:
            if cell.row == row and cell.column == column and cell.sheet_name == sheet_name:
                cell.update_access_time()
                return cell
        return None
    
    def get_cell_by_reference(self, cell_reference: str, sheet_name: str = None) -> Optional[Cell]:
        """
        Get a cell by its Excel-style reference (e.g., "A1", "B2").
        
        Args:
            cell_reference: The Excel-style cell reference.
            sheet_name: The name of the sheet (defaults to active_sheet if None).
            
        Returns:
            The Cell object if found, None otherwise.
        """
        if sheet_name is None:
            sheet_name = self.active_sheet
            
        # First try to find an exact match
        for cell in self.cells:
            # Handle case where sheet_name might be None in the cell
            cell_sheet = cell.sheet_name or self.active_sheet
            
            if cell.cell_reference == cell_reference and cell_sheet == sheet_name:
                cell.update_access_time()
                return cell
                
        # If no exact match is found, try again ignoring sheet_name
        # This is a fallback for older data where sheet_name might not have been set
        for cell in self.cells:
            if cell.cell_reference == cell_reference:
                # If we find a match, update the sheet_name to be correct going forward
                if not cell.sheet_name:
                    cell.sheet_name = sheet_name
                cell.update_access_time()
                return cell
                
        return None
    
    def __str__(self) -> str:
        return f"Spreadsheet: {self.name} ({len(self.cells)} cells)" 