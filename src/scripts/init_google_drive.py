
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import json
import argparse
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "secrets/google_credentials.json"

def init_drive():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder_url", help="URL of the shared Google Drive folder")
    args = parser.parse_args()

    try:
        logger.info("Authenticating with Google...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        
        folder_id = None
        if args.folder_url:
            # Extract ID from URL: https://drive.google.com/drive/folders/1...?...
            match = re.search(r'folders/([a-zA-Z0-9_-]+)', args.folder_url)
            if match:
                folder_id = match.group(1)
                logger.info(f"Targeting Shared Folder ID: {folder_id}")
            else:
                logger.error("Invalid folder URL format")
                return
        
        # Define the files structure
        files_to_create = {
            "1. Master TechCards 🍲": [
                ["Dish Name", "Ingredient Name", "Gross (Amount)", "Unit", "Netto", "Comment"],
                ["Soup Pho", "Beef", 0.150, "kg", 0.120, "Example Entry"],
                ["Soup Pho", "Noodles", 0.200, "kg", 0.200, "Rice noodles"]
            ],
            "2. Sales Forecast 📅": [
                ["Period (Month/Week)", "Outlet", "Expected Revenue (RUB)", "Comment"],
                ["Jan-2026", "Danilovsky", 6942327, "From Excel Forecast"],
                ["Jan-2026", "Depo", 8000000, "Optimistic"]
            ],
            "3. Product Mix 📊": [
                ["Dish Name", "Share of Revenue (%)", "Avg Price (RUB)", "Category"],
                ["Soup Pho", 0.05, 650, "Soup"],
                ["Mango Shake", 0.02, 450, "Drinks"]
            ],
            "4. DRAFT ORDER 🛒": [
                ["Ingredient", "Required (Raw)", "Unit", "Pkg Size", "Order Qty", "Order Unit", "Logic/Comment"],
                ["-- System Generated --", "--", "--", "--", "--", "--", "--"]
            ]
        }
        
        created_links = {}
        
        for filename, data in files_to_create.items():
            logger.info(f"Creating sheet: {filename}")
            try:
                if folder_id:
                    # gspread create with folder_id
                    sh = client.create(filename, folder_id=folder_id)
                else:
                    sh = client.create(filename)
                
                # Share with anyone with link if not in shared folder (or just to be safe)
                # If in shared folder, it inherits permissions usually, but 'anyone with link' is safer for user to open immediately
                try:
                    sh.share(None, perm_type='anyone', role='writer')
                except Exception as share_err:
                    logger.warning(f"Could not set 'anyone' permission (might be restricted by domain): {share_err}")
                
                ws = sh.sheet1
                ws.clear()
                ws.update(range_name="A1", values=data)
                
                # Formatting (Bold Headers)
                try:
                    ws.format('A1:Z1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
                except Exception:
                    pass # Ignore formatting errors on restricted accounts
                
                created_links[filename] = sh.url
                logger.info(f"Created: {sh.url}")
                
            except Exception as e:
                logger.error(f"Failed to create {filename}: {e}")

        if created_links:
            print("\n" + "="*50)
            print("✅ GOOGLE DRIVE SETUP COMPLETE")
            print("Please save these links or organize them into a folder on your Drive:")
            for name, url in created_links.items():
                print(f"{name}: {url}")
            print("="*50 + "\n")
        else:
            print("\n❌ Failed to create any files. Check Quota or Permissions.")

    except Exception as e:
        logger.error(f"Critical Error: {e}")

if __name__ == "__main__":
    init_drive()
