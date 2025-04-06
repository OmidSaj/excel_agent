import formulas
from typing import Dict, List, Optional, Tuple
from db.models import Cell, Spreadsheet
import re

def expand_cell_range(range_ref: str) -> List[str]:
    """
    Expand a cell range reference (e.g., "B1:C10", "$B$1:$C$10") into a list of individual cell references.
    
    Args:
        range_ref: The cell range reference (e.g., "B1:C10", "A1:A5", "B1:D1", "$B$1:$C$10")
        
    Returns:
        List of individual cell references in the range
    """
    # Handle sheet-qualified ranges (e.g., "Sheet1!B1:C10")
    sheet_name = None
    if '!' in range_ref:
        sheet_name, range_ref = range_ref.split('!')
        sheet_name = sheet_name.lower()
    
    # Split the range into start and end cells
    start_cell, end_cell = range_ref.split(':')
    
    # Extract column letters and row numbers, handling $ signs
    start_col = re.match(r'\$?([A-Z]+)', start_cell).group(1)
    start_row = int(re.match(r'\$?[A-Z]+\$?(\d+)', start_cell).group(1))
    end_col = re.match(r'\$?([A-Z]+)', end_cell).group(1)
    end_row = int(re.match(r'\$?[A-Z]+\$?(\d+)', end_cell).group(1))
    
    # Convert column letters to numbers (A=1, B=2, ..., Z=26, AA=27, etc.)
    def col_to_num(col: str) -> int:
        num = 0
        for c in col:
            num = num * 26 + (ord(c) - ord('A') + 1)
        return num
    
    # Convert numbers back to column letters
    def num_to_col(num: int) -> str:
        col = ''
        while num > 0:
            num, remainder = divmod(num - 1, 26)
            col = chr(65 + remainder) + col
        return col
    
    start_col_num = col_to_num(start_col)
    end_col_num = col_to_num(end_col)
    
    # Generate all cell references in the range
    cells = []
    for col_num in range(start_col_num, end_col_num + 1):
        for row in range(start_row, end_row + 1):
            # Preserve $ signs from original reference if present
            col_prefix = '$' if '$' in start_cell.split(str(start_row))[0] else ''
            row_prefix = '$' if f'${start_row}' in start_cell else ''
            cell_ref = f"{col_prefix}{num_to_col(col_num)}{row_prefix}{row}"
            if sheet_name:
                cell_ref = f"{sheet_name}!{cell_ref}"
            cells.append(cell_ref)
    return cells

def extract_formula_inputs(formula: str) -> Dict[str, Optional[str]]:
    """
    Extract input cell references from an Excel formula.
    
    Args:
        formula: The Excel formula string (should include the leading '=')
        
    Returns:
        Dictionary mapping cell references to their range objects (or None for non-cell inputs)
    """
    try:
        parser = formulas.Parser()
        ast_result = parser.ast(formula)
        if not ast_result or len(ast_result) < 2:
            return {}
            
        func = ast_result[1].compile()
        return func.inputs
    except Exception as e:
        print(f"Error parsing formula {formula}: {str(e)}")
        return {}

def update_cell_dependencies(spreadsheet: Spreadsheet, cell: Cell, workbook_name: str = None, reverse_alias_mapping: Dict[str, Dict[str, str]] = None) -> None:
    """
    Update the dependencies for a cell containing a formula.
    This includes:
    1. Extracting inputs from the formula
    2. Adding these as precedents to the current cell
    3. Adding the current cell as a dependent to each input cell
    
    Args:
        spreadsheet: The Spreadsheet document containing the cell
        cell: The Cell document containing the formula
        workbook_name: The name of the workbook containing the cell
        reverse_alias_mapping: Dictionary mapping aliases to cell references, used for resolving aliases in formulas
    """
    if not cell.formula:
        return
        
    # Extract inputs from the formula
    inputs = extract_formula_inputs(cell.formula)
    
    # Process each input
    for cell_ref, _ in inputs.items():
        # Skip non-cell inputs (like constants)
        if not cell_ref or cell_ref.isdigit():
            continue
            
        # Check if this is an alias and resolve it to a standard cell reference
        if reverse_alias_mapping and cell_ref in reverse_alias_mapping:
            alias_info = reverse_alias_mapping[cell_ref]
            sheet_name = alias_info['sheet_name']
            cell_ref = alias_info['cell_ref']
        else:
            # Handle sheet-qualified references (e.g., "Sheet1!A1")
            sheet_name = cell.sheet_name  # Default to the current cell's sheet name
            if '!' in cell_ref:
                sheet_name, cell_ref = cell_ref.split('!')
            
        # Check if this is a range reference (e.g., "B1:C10")
        if ':' in cell_ref:
            # Expand the range into individual cell references
            expanded_cells = expand_cell_range(f"{sheet_name}!{cell_ref}" if sheet_name else cell_ref)
            
            # Add each cell in the range as a precedent
            for expanded_cell in expanded_cells:
                exp_sheet_name = sheet_name  # Default to the current sheet name
                exp_cell_ref = expanded_cell
                if '!' in expanded_cell:
                    exp_sheet_name, exp_cell_ref = expanded_cell.split('!')
                
                # Add the precedent to the current cell
                cell.add_precedent(exp_cell_ref, exp_sheet_name, workbook_name)
                cell.formula_inputs.append(exp_cell_ref)
                
                # Find the input cell and add current cell as its dependent
                input_cell = spreadsheet.get_cell_by_reference(exp_cell_ref, exp_sheet_name)
                if input_cell:
                    # Ensure the input cell has a sheet_name
                    if not input_cell.sheet_name:
                        input_cell.sheet_name = exp_sheet_name
                    input_cell.add_dependent(cell.cell_reference, cell.sheet_name, workbook_name)
        else:
            # Handle single cell reference
            cell.add_precedent(cell_ref, sheet_name, workbook_name)
            cell.formula_inputs.append(cell_ref)
            
            # Find the input cell and add current cell as its dependent
            input_cell = spreadsheet.get_cell_by_reference(cell_ref, sheet_name)
            if input_cell:
                # Ensure the input cell has a sheet_name
                if not input_cell.sheet_name:
                    input_cell.sheet_name = sheet_name
                input_cell.add_dependent(cell.cell_reference, cell.sheet_name, workbook_name)
            
    # Save the changes
    spreadsheet.save() 