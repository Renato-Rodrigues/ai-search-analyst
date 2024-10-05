import sqlite3
from typing import Any, Dict, List, Union
from io_utils.google_sheets import GoogleSheetsIO
import pandas as pd

class IODatabase:
    def __init__(self, db_path: str = 'io_operations.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS io_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT,
            sheet_name TEXT,
            data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()

    def save_operation(self, operation_type: str, sheet_name: str, data: Any):
        # Delete previous entries for the same operation_type and sheet_name
        self.cursor.execute('''
        DELETE FROM io_operations
        WHERE operation_type = ? AND sheet_name = ?
        ''', (operation_type, sheet_name))

        # Insert new entry
        self.cursor.execute('''
        INSERT INTO io_operations (operation_type, sheet_name, data)
        VALUES (?, ?, ?)
        ''', (operation_type, sheet_name, str(data)))
        self.conn.commit()

    def get_last_operation(self, operation_type: str, sheet_name: str) -> Union[Dict, None]:
        self.cursor.execute('''
        SELECT data FROM io_operations
        WHERE operation_type = ? AND sheet_name = ?
        ORDER BY timestamp DESC
        LIMIT 1
        ''', (operation_type, sheet_name))
        result = self.cursor.fetchone()
        return eval(result[0]) if result else None

class IOService:
    def __init__(self):
        self.db = IODatabase()
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
            for sheet_name,value in dic.items():
                # Check if value is empty or contains only None
                if not value or all(v is None for v in value):
                    print(f"No valid data to save for sheet '{sheet_name}'. Skipping...")
                    continue  # Skip this sheet if there's no valid data
                try:
                    df = pd.DataFrame(value)
                except ValueError as e:
                    print(f"Error concatenating data for sheet '{sheet_name}': {e}")
                    continue
                # Ensure sheet name is valid (max 31 characters, no special characters)
                sheet_name = ''.join(c for c in sheet_name if c.isalnum() or c in (' ', '_'))[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"Results for '{sheet_name}' saved to sheet in {excel_filename}")


    def get_value(self, sheet_name: str, output_mode: str = 'default') -> Union[List[List[str]], List[Dict[str, Any]], List[Dict[str, List[str]]]]:
        data = self.io.get_value(sheet_name, output_mode)
        # Overwrite the database value
        self.db.save_operation('read', sheet_name, data)
        return data

    def set_value(self, value: Any, sheet_name: str, column: str, row: int = None, value_type: str = 'string', write_headers: bool = True):
        if sheet_name not in self.cleared_sheets:
            self.ensure_sheet_exists(sheet_name, clear_if_exists=True)
            self.cleared_sheets.add(sheet_name)
        
        self.io.set_value(value, sheet_name, column, row, value_type, write_headers, self.cleared_sheets)
        self.db.save_operation('write', sheet_name, {'value': value, 'column': column, 'row': row, 'type': value_type, 'write_headers': write_headers})

    def find_row_with_content(self, sheet_name: str, column: str) -> int:
        row = self.io.find_row_with_content(sheet_name, column)
        self.db.save_operation('find_row', sheet_name, {'column': column, 'row': row})
        return row

    def ensure_sheet_exists(self, sheet_name: str, clear_if_exists: bool = False):
        result = self.io.ensure_sheet_exists(sheet_name, clear_if_exists, self.cleared_sheets)
        self.db.save_operation('ensure_sheet', sheet_name, {'clear_if_exists': clear_if_exists})
        return result

io_service = IOService()


