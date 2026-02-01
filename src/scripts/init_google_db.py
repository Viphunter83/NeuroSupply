
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import argparse
import re
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "secrets/google_credentials.json"

def init_db():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet_url", help="URL of the NeuroSupply Database sheet", required=True)
    args = parser.parse_args()

    try:
        logger.info("Authenticating with Google...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        
        # Strategy 1: Open by Key
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', args.sheet_url)
        sheet_id = match.group(1) if match else None
        
        sh = None
        
        # Robust open strategy
        try:
            if sheet_id:
                logger.info(f"Attempting open_by_key: {sheet_id}")
                sh = client.open_by_key(sheet_id)
        except Exception as e:
            logger.warning(f"open_by_key failed: {e}. Trying by title match...")
            
        if not sh:
            # Fallback: List and find
            files = client.list_spreadsheet_files()
            for f in files:
                # API returns 'name' and 'id'
                if f['id'] == sheet_id or f['name'] == "NeuroSupply Database":
                    logger.info(f"Found file in list: {f['name']} ({f['id']})")
                    sh = client.open_by_key(f['id'])
                    break
        
        if not sh:
             logger.error("Could not open spreadsheet by ID or Title.")
             return

        logger.info(f"Successfully opened: {sh.title}")
        
        # Define Tabs
        sheets_config = {
            "1. TechCards": [
                ["Dish Name", "Ingredient Name", "Gross (Amount)", "Unit", "Netto", "Comment"],
                ["Soup Pho", "Beef", 0.150, "kg", 0.120, "Example"],
                ["Soup Pho", "Noodles", 0.200, "kg", 0.200, "Rice noodles"]
            ],
            "2. Sales Forecast": [
                ["Period (Month/Week)", "Outlet", "Expected Revenue (RUB)", "Comment"],
                ["Jan-2026", "Danilovsky", 6942327, "From Excel Forecast"],
                ["Jan-2026", "Depo", 8000000, "Optimistic"]
            ],
            "3. Product Mix": [
                ["Dish Name", "Share of Revenue (%)", "Avg Price (RUB)", "Category"],
                ["Soup Pho", 0.05, 650, "Soup"],
                ["Mango Shake", 0.02, 450, "Drinks"]
            ],
            "4. DRAFT ORDER": [
                ["Ingredient", "Required (Raw)", "Unit", "Pkg Size", "Order Qty", "Order Unit", "Logic/Comment"],
                ["-- System Generated --", "--", "--", "--", "--", "--", "--"]
            ]
        }
        
        existing_titles = [ws.title for ws in sh.worksheets()]
        
        for title, data in sheets_config.items():
            if title in existing_titles:
                logger.info(f"Tab '{title}' already exists. Skipping.")
            else:
                logger.info(f"Creating tab: {title}")
                ws = sh.add_worksheet(title=title, rows=100, cols=20)
                ws.update(range_name="A1", values=data)
                
                # Formatting
                try:
                    ws.format('A1:Z1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
                except Exception:
                    pass

        print(f"\n✅ DATABASE INITIALIZED: {sh.title}")
        print("Tabs created: " + ", ".join(sheets_config.keys()))

    except Exception as e:
        logger.error(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_db()
