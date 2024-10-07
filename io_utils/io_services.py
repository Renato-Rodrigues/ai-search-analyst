from typing import Any, Dict, List, Union
from io_utils.google_sheets import GoogleSheetsIO
import pandas as pd

class IOService:
    def __init__(self):
        self.cleared_sheets = set()
        self.io = GoogleSheetsIO()

    def save_to_excel(self, excel_filename, dic):
        """
        Saves dictionary to an Excel file.

        :param excel_filename: The name of the Excel file to save the results.
        :param dic: Dictionary containing sheet names as keys and sheet content as value.
        """
        
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            # Save each query result to its own sheet
            for sheet_name, value in dic.items():
                # Check if value is empty or contains only None
                if not value or all(v is None for v in value):
                    print(f"[Excel] No valid data to save for sheet '{sheet_name}'. Skipping...")
                    continue  # Skip this sheet if there's no valid data
                try:
                    df = pd.DataFrame(value)
                except ValueError as e:
                    print(f"[Excel] Error concatenating data for sheet '{sheet_name}': {e}")
                    continue
                # Ensure sheet name is valid (max 31 characters, no special characters)
                sheet_name = ''.join(c for c in sheet_name if c.isalnum() or c in (' ', '_'))[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"[Excel] Results for '{sheet_name}' saved to sheet in {excel_filename}")

    def get_value(self, sheet_name: str, output_mode: str = 'default') -> Union[List[List[str]], List[Dict[str, Any]], List[Dict[str, List[str]]]]:
        return self.io.get_value(sheet_name, output_mode)

    def set_value(self, value: Any, sheet_name: str, column: str, row: int = None, value_type: str = 'string', write_headers: bool = True):
        if sheet_name not in self.cleared_sheets:
            self.ensure_sheet_exists(sheet_name, clear_if_exists=True)
            self.cleared_sheets.add(sheet_name)
        
        self.io.set_value(value, sheet_name, column, row, value_type, write_headers, self.cleared_sheets)

    def find_row_with_content(self, sheet_name: str, column: str) -> int:
        return self.io.find_row_with_content(sheet_name, column)

    def ensure_sheet_exists(self, sheet_name: str, clear_if_exists: bool = False):
        return self.io.ensure_sheet_exists(sheet_name, clear_if_exists, self.cleared_sheets)

io_service = IOService()
