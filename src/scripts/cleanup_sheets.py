
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "secrets/google_credentials.json"
SHEET_ID = "1mgqHPyqLZsDME4zxEds2XVPdxpVCmhM5zYdbfn62hqM"

VALID_TITLES = [
    "0. ИНСТРУКЦИЯ ℹ️",
    "1. ТЕХКАРТЫ 🍲",
    "2. ПЛАН ПРОДАЖ 📅",
    "3. ПРОДУКТОВЫЙ МИКС 📊",
    "4. ЧЕРНОВИК ЗАКАЗА 🛒"
]

def add_filter_view(ws):
    # Determine the last column letter based on header (assumes row 1 is header)
    try:
        # Get number of cols
        cols = ws.col_count
        # Simple A1 notation for whole sheet or just headers
        # Use batch_update to set basic filter
        body = {
            "requests": [
                {
                    "setBasicFilter": {
                        "filter": {
                            "range": {
                                "sheetId": ws.id,
                                "startRowIndex": 0,
                                # "endRowIndex": 1000, # Optional: cover all
                                "startColumnIndex": 0,
                                "endColumnIndex": cols
                            }
                        }
                    }
                }
            ]
        }
        ws.spreadsheet.batch_update(body)
        logger.info(f"Filter added to {ws.title}")
    except Exception as e:
        logger.warning(f"Could not add filter to {ws.title}: {e}")

def cleanup():
    try:
        logger.info("Authenticating...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        
        logger.info(f"Opening Sheet ID: {SHEET_ID}")
        sh = client.open_by_key(SHEET_ID)

        worksheets = sh.worksheets()
        
        # 1. Delete Unwanted Tabs
        for ws in worksheets:
            if ws.title not in VALID_TITLES:
                logger.info(f"Deleting obsolete tab: {ws.title}")
                try:
                    sh.del_worksheet(ws)
                except Exception as e:
                    logger.error(f"Error deleting {ws.title}: {e}")
            else:
                logger.info(f"Keeping valid tab: {ws.title}")

        # 2. Add Filters to Valid Tabs (except Instruction)
        for title in VALID_TITLES:
            if title == "0. ИНСТРУКЦИЯ ℹ️":
                continue
            
            try:
                ws = sh.worksheet(title)
                # Clear existing filter first? setBasicFilter usually overwrites or we can clear
                # Let's just set it.
                add_filter_view(ws)
            except gspread.WorksheetNotFound:
                logger.warning(f"Tab not found: {title}")

        print("\n✅ CLEANUP & FILTERS APPLIED!")

    except Exception as e:
        logger.error(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup()
