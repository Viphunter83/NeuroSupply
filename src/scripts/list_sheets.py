
import sys
import os
import asyncio
import logging
sys.path.append(os.getcwd())
from src.services.data_loader.sheets_client import SheetsClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_titles():
    sheets = SheetsClient(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
    sh = sheets.client.open_by_key(sheets.sheet_id)
    for ws in sh.worksheets():
        logger.info(f"Sheet: '{ws.title}'")

if __name__ == "__main__":
    list_titles()
