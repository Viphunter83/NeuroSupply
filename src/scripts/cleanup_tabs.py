
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

def cleanup_tabs():
    try:
        logger.info("Authenticating...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        # Target: "НАСТРОЙКИ ⚙️" (The one without "5.")
        try:
            ws_old = sh.worksheet("НАСТРОЙКИ ⚙️")
            logger.info(f"Found old tab: {ws_old.title} (ID: {ws_old.id})")
            
            # Double check it is NOT the new one
            if ws_old.title == "5. НАСТРОЙКИ ⚙️":
                logger.warning("Safety check: Found tab is likely the new one. Aborting.")
                return

            sh.del_worksheet(ws_old)
            logger.info("✅ Deleted old 'НАСТРОЙКИ ⚙️' tab.")
            
        except gspread.WorksheetNotFound:
            logger.info("Old 'НАСТРОЙКИ ⚙️' tab not found. Already clean.")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    cleanup_tabs()
