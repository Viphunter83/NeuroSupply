
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

def list_tabs():
    try:
        logger.info("Authenticating...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        worksheets = sh.worksheets()
        print("\n📂 CURRENT TABS:")
        for ws in worksheets:
            print(f"- '{ws.title}' (ID: {ws.id})")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    list_tabs()
