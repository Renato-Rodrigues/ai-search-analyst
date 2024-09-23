import sqlite3
from typing import Any, Dict, List, Union
from io_utils.google_sheets_io import get_google_sheets_value, set_google_sheets_value, ensure_sheet_exists, find_row_with_content, clear_sheet

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

    def get_value(self, sheet_name: str, output_mode: str = 'list_dict_column') -> Union[List[Dict], Dict]:
        cached_data = self.db.get_last_operation('read', sheet_name)
        if cached_data:
            return cached_data
        
        data = get_google_sheets_value(sheet_name, output_mode)
        self.db.save_operation('read', sheet_name, data)
        return data

    def set_value(self, value: Any, sheet_name: str, column: str, row: int = None, value_type: str = 'string', write_headers: bool = True, clear_sheet: bool = False):
        if clear_sheet and sheet_name not in self.cleared_sheets:
            self.clear_sheet(sheet_name)
            self.cleared_sheets.add(sheet_name)
        
        set_google_sheets_value(value, sheet_name, column, row, value_type, write_headers=write_headers)
        self.db.save_operation('write', sheet_name, {'value': value, 'column': column, 'row': row, 'type': value_type, 'write_headers': write_headers})

    def find_row_with_content(self, sheet_name: str, column: str) -> int:
        row = find_row_with_content(sheet_name, column)
        self.db.save_operation('find_row', sheet_name, {'column': column, 'row': row})
        return row

    def ensure_sheet_exists(self, sheet_name: str, clear_if_exists: bool = False):
        ensure_sheet_exists(sheet_name, clear_if_exists=clear_if_exists)
        self.db.save_operation('ensure_sheet', sheet_name, {'clear_if_exists': clear_if_exists})

    def clear_sheet(self, sheet_name: str):
        clear_sheet(sheet_name)
        self.db.save_operation('clear_sheet', sheet_name, {})

io_service = IOService()


