import gspread
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """
    A wrapper for gspread to simplify interactions with Google Sheets.
    Includes methods to get values, append rows, and update specific cells.
    """
    def __init__(self, service_account_path: str, spreadsheet_id: str):
        try:
            self.gc = gspread.service_account(filename=service_account_path)
            self.spreadsheet = self.gc.open_by_key(spreadsheet_id)
            logger.info("Successfully connected to Google Sheets.")
        except Exception as e:
            logger.error(f"Failed to authenticate or open the Google Sheet: {e}")
            raise

    def get_worksheet(self, sheet_name: str) -> gspread.Worksheet:
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet with name '{sheet_name}' was not found.")
            raise

    def get_column_values(self, worksheet: gspread.Worksheet, column_index: int) -> set:
        try:
            values = worksheet.col_values(column_index)
            # The first value is the header; we remove it.
            return set(values[1:]) if values else set()
        except Exception as e:
            logger.error(f"Error retrieving column values: {e}")
            raise

    def get_header_map(self, worksheet: gspread.Worksheet) -> dict:
        """
        Reads the first row (headers) and returns a dictionary mapping
        header names to their column numbers (1-indexed).
        """
        try:
            headers = worksheet.row_values(1)
            logger.info(f"Headers read from Google Sheet: {headers}")
            return {header.strip(): i + 1 for i, header in enumerate(headers)}
        except Exception as e:
            logger.error(f"Error reading sheet headers: {e}")
            return {}

    def get_all_values(self, worksheet: gspread.Worksheet) -> list:
        """
        Fetches all data from the worksheet as a list of lists.
        """
        try:
            return worksheet.get_all_values()
        except Exception as e:
            logger.error(f"Error retrieving all values from sheet: {e}")
            return []

    def update_cell(self, worksheet: gspread.Worksheet, row: int, col: int, value: str):
        """
        Updates a single cell in the worksheet.
        Note: row and col are 1-indexed.
        """
        try:
            worksheet.update_cell(row, col, value)
            logger.debug(f"Updated cell at (Row {row}, Col {col}) with value: '{value}'")
        except Exception as e:
            logger.error(f"Error updating cell at (Row {row}, Col {col}): {e}")
            # Do not re-raise, as a single update failure shouldn't stop a whole campaign.

    def append_row(self, worksheet: gspread.Worksheet, row_data: list):
        try:
            worksheet.append_row(row_data)
        except Exception as e:
            logger.error(f"Error appending row to sheet: {e}")
            raise
