# Google Sheets I/O operations

from config import config
from io_utils.google_sheets_auth import get_google_sheets_credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

class GoogleSheetsIO:
    def __init__(self):
        self.spreadsheet_id = config['io']['googleSheets']['spreadsheet_id']
        self.creds = get_google_sheets_credentials()
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_value(self, range_name, output_mode='default'):
        """
        Fetches range values from a Google Sheet.
        
        :param range_name: The range to fetch from the Google Sheet
        :param output_mode: 'default' for original behavior, 'list_dict' for list of dictionaries or 'list_dict_column' for list of dictionary form columns
        :return: List of values, dictionary, or list of dictionaries depending on output_mode
        """
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        if output_mode == 'default':
            if values and all(len(row) == 1 for row in values): # Simplify the result if it's a single column
                return [row[0] if row else '' for row in values]
            return values
        elif output_mode == 'list_dict':
            if len(values) < 2:
                return []
            
            headers = values[0]
            result = []
            for row in values[1:]:
                row_dict = {headers[i]: (row[i] if i < len(row) else '') for i in range(len(headers))}
                result.append(row_dict)
            
            return result
        elif output_mode == 'list_dict_column':
            if not values:
                return []
            
            headers = values[0]
            result = []
            for col in range(len(headers)):
                column_values = [row[col] if col < len(row) else '' for row in values[1:]]
                result.append({headers[col]: column_values})
            
            return result
        else:
            raise ValueError("Invalid output_mode. Use 'default', 'list_dict' or 'list_dict_column'.")

    def set_value(self, value, sheet_name, column, row=None, value_type='string', write_headers=True, cleared_sheets=None):
        # Input validation and preprocessing
        if value_type == 'table':
            if isinstance(value, dict):
                if 'error' in value and 'raw_response' in value:
                    # Parse the raw_response
                    try:
                        raw_data = json.loads(value['raw_response'])
                        value = [dict(zip(raw_data.keys(), values)) for values in zip(*raw_data.values())]
                    except json.JSONDecodeError:
                        value = [{"Error": "Failed to parse raw_response"}]
                elif all(isinstance(v, list) for v in value.values()):
                    # Convert dict of lists to list of dicts
                    value = [dict(zip(value.keys(), values)) for values in zip(*value.values())]
                else:
                    # Treat single dictionary as a table with one row
                    value = [value]
            if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
                value = [{"Error": "Invalid table format"}]
        
        elif value_type == 'string':
            value = [str(value)]
        else:
            value = value if isinstance(value, list) else [value]

        # Prepare values for writing
        if value_type == 'table':
            headers = list(value[0].keys())
            if write_headers:
                values_to_write = [headers] + [[str(item.get(header, '')) for header in headers] for item in value]
            else:
                values_to_write = [[str(item.get(header, '')) for header in headers] for item in value]
        else:
            values_to_write = [[str(item) for item in value]]

        # Google Sheets API operations
        # Check if sheet exists, if not create it, and clear if necessary
        if not self.ensure_sheet_exists(sheet_name, cleared_sheets=cleared_sheets):
            raise Exception(f"Failed to ensure sheet '{sheet_name}' exists")

        # Determine the row to write if not provided
        if row is None:
            row = 1 if (last_row := self.find_row_with_content(sheet_name, column, content='last')) == 1 else last_row + 2

        # Determine the range to write
        start_cell = f"{column}{row}"
        end_column = chr(ord(column) + len(values_to_write[0]) - 1)
        end_row = row + len(values_to_write) - 1
        range_name = f"'{sheet_name}'!{start_cell}:{end_column}{end_row}"

        # Prepare the value range object
        value_range_body = {
            "majorDimension": "ROWS",
            "values": values_to_write
        }

        # Write the values to the sheet
        try:
            request = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=value_range_body
            )
            response = request.execute()
            print(f"Data written to '{sheet_name}'!{start_cell}")
            return response
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def ensure_sheet_exists(self, sheet_name, clear_if_exists=False, cleared_sheets=None):
        """
        Checks if a sheet exists, creates it if it doesn't, and optionally clears it if it does.

        :param sheet_name: Name of the sheet to check/create
        :param clear_if_exists: If True, clear the sheet if it already exists
        :param cleared_sheets: Set of sheets that have been cleared
        :return: True if the sheet existed or was created successfully, False otherwise
        """

        # Google Sheets API operations
        try:
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_exists = any(sheet['properties']['title'] == sheet_name for sheet in sheet_metadata.get('sheets', []))
            
            if not sheet_exists:
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }]
                }
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request_body
                ).execute()
                print(f"Sheet '{sheet_name}' created.")
            elif clear_if_exists and (cleared_sheets is None or sheet_name not in cleared_sheets):
                # Clear the existing sheet
                clear_range = f"'{sheet_name}'!A1:ZZ"
                self.service.spreadsheets().values().clear(
                    spreadsheetId=self.spreadsheet_id,
                    range=clear_range,
                    body={}
                ).execute()
                if cleared_sheets is not None:
                    cleared_sheets.add(sheet_name)
                print(f"Sheet '{sheet_name}' cleared.")
            
            return True
        except HttpError as error:
            print(f"An error occurred while checking/creating/clearing the sheet: {error}")
            return False

    def find_row_with_content(self, sheet_name, column, content='last'):
        """
        Finds the row with specific content in a specific column of a Google Sheet.
        If content is 'last', finds the last row with content.

        :param sheet_name: Name of the sheet
        :param column: Column letter (e.g., 'A', 'B', 'C')
        :param content: The content to search for, or 'last' to find the last row with content
        :return: Row number of the cell containing the content, or 0 if not found
        """
        try:
            # Get all values in the specified column
            range_name = f"'{sheet_name}'!{column}:{column}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            values = result.get('values', [])
            
            if content == 'last':
                # Find the last non-empty row
                for i in range(len(values) - 1, -1, -1):
                    if values[i] and values[i][0].strip():  # Check if the cell is not empty or just whitespace
                        return i + 1  # Adding 1 because sheet rows are 1-indexed
            else:
                # Find the row with the specific content
                for i, row in enumerate(values):
                    if row and row[0].strip() == content:  # Check if the cell matches the content
                        return i + 1  # Adding 1 because sheet rows are 1-indexed
            
            # If the content is not found or all rows are empty
            return 0
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def clear_sheet(self, sheet_name):
        """
        Clears all content from a specified sheet.

        :param sheet_name: Name of the sheet to clear
        """
        try:
            # Clear the entire sheet
            clear_range = f"'{sheet_name}'!A1:ZZ"
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=clear_range,
                body={}
            ).execute()
            print(f"Sheet '{sheet_name}' cleared.")
        except HttpError as error:
            print(f"An error occurred while clearing the sheet: {error}")
            raise

# Create a single instance of GoogleSheetsIO
google_sheets_io = GoogleSheetsIO()



