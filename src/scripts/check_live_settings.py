
import asyncio
import os
import sys
import logging

sys.path.append(os.getcwd())

from src.services.data_loader.sheets_client import SheetsClient

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveSettingsCheck")

def check_settings():
    # Real Spreadsheet ID
    SHEET_ID = "1mgqHPyqLZsDME4zxEds2XVPdxpVCmhM5zYdbfn62hqM"
    
    logger.info("Connecting to Google Sheets...")
    client = SheetsClient(SHEET_ID)
    
    logger.info("Reading '5. НАСТРОЙКИ ⚙️'...")
    settings = client.fetch_settings()
    
    print("\n" + "="*40)
    print("📡 LIVE SETTINGS DETECTED:")
    print(f"   🏢 Active Restaurant ID: '{settings.get('active_restaurant_id')}'")
    print(f"   🛡️ Safety Stock Ratio:   {settings.get('safety_stock')}x")
    print(f"   🚚 Days in Transit:      {settings.get('days_in_transit')} days")
    print("="*40 + "\n")

if __name__ == "__main__":
    check_settings()
