def col_to_num(col: str) -> int:
    """Convert Excel column letters (e.g. 'AB') to a 1-indexed column number."""
    num = 0
    for c in col:
        num = num * 26 + (ord(c.upper()) - ord('A') + 1)
    return num

def num_to_col(num: int) -> str:
    """Convert a 1-indexed column number to Excel column letters (e.g. 28 -> 'AB')."""
    col = ""
    while num:
        num, remainder = divmod(num - 1, 26)
        col = chr(65 + remainder) + col
    return col
def get_excel_tile(cell: str, distance: int) -> list[list[str]]:
    """
    Given an Excel cell address (e.g. 'D3' or 'AB12') and a distance,
    returns a tile (list of lists) of cell addresses within the given
    distance of the cell. If the region would extend beyond the spreadsheet 
    edges, it is clamped accordingly.
    
    Example:
    get_excel_tile('D3', 1) -> [['C2', 'D2', 'E2'], 
                                ['C3', 'D3', 'E3'], 
                                ['C4', 'D4', 'E4']]
    For a corner cell like A1 with distance 1, it returns:
    [['A1', 'B1'],
     ['A2', 'B2']]
    """
    
    MAX_COL = 16384  # Excel's maximum column number (XFD)
    MAX_ROW = 1048576  # Excel's maximum row number

    # Split the cell into its column (letters) and row (digits) parts.
    col_part = "".join(filter(str.isalpha, cell))
    row_part = "".join(filter(str.isdigit, cell))
    
    center_col = col_to_num(col_part)
    center_row = int(row_part)
    
    # Clamp boundaries to the valid range instead of shifting the window.
    left = max(1, center_col - distance)
    right = min(MAX_COL, center_col + distance)
    top = max(1, center_row - distance)
    bottom = min(MAX_ROW, center_row + distance)
    
    # Build the tile as a list of lists.
    tile = []
    for r in range(top, bottom + 1):
        row_cells = []
        for c in range(left, right + 1):
            cell_addr = num_to_col(c) + str(r)
            row_cells.append(cell_addr)
        tile.append(row_cells)
    
    return tile

def get_excel_tile_data(cell_id, sheetname, db,spreadsheet_name,distance =2):
    """
    Convert a nested list of Excel cell ids and a dictionary of cell contents into a Markdown table.
    
    Parameters:
      cell_id (str): The cell id of the top-left cell in the table (e.g., "A1").
      sheetname (str): The name of the sheet where the table is located.
      cell_data (dict): Dictionary mapping sheets and cell ids to cell contents. for example
      cell_data[sheetname][cell_id] = cell_content
      
    Returns:
      str: A Markdown formatted table.
    """
    spreadsheet_data = db.get_spreadsheet_data(name=spreadsheet_name,as_dict=True)
    cell_references = spreadsheet_data['cell_references'][sheetname]
    nested_list = get_excel_tile(cell_id, distance)
    # Extract column headers from the first row by taking the alphabetical part.
    first_row = nested_list[0]
    columns = [''.join(filter(str.isalpha, cell)) for cell in first_row]
    
    # Extract row labels for each row by taking the numeric part of the first cell in each row.
    row_labels = [''.join(filter(str.isdigit, row[0])) for row in nested_list]
    
    # Build header for the markdown table with an empty top-left cell.
    header_line = "|   | " + " | ".join(columns) + " |"
    # Create the markdown separator line.
    separator_line = "|---|" + "|".join(["---"] * len(columns)) + "|"
    
    # Start building the output lines.
    lines = [header_line, separator_line]
    
    # Build each row in the table.
    for row, row_label in zip(nested_list, row_labels):
        # For each cell, get the content or an empty string if not present.
        cell_values = []
        for cell_ref in row:
            if cell_ref in cell_references:
                cell_data = db.get_cell_data(cell_ref, sheetname)
                cell_values.append(str(cell_data['value']['raw']))
            else:
                cell_values.append("")
        row_line = f"| {row_label} | " + " | ".join(cell_values) + " |"
        lines.append(row_line)
    
    # Join all lines into a single Markdown string.
    return "\n".join(lines)