
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "secrets/google_credentials.json"
SHEET_ID = "1mgqHPyqLZsDME4zxEds2XVPdxpVCmhM5zYdbfn62hqM"
EXCEL_PATH = "data_samples/Прогноз ТО 2026 (2) (2).xlsx"

def import_sales_plan():
    if not os.path.exists(EXCEL_PATH):
        logger.error(f"Excel file not found: {EXCEL_PATH}")
        return

    try:
        # 1. Read Excel
        logger.info(f"Reading Excel: {EXCEL_PATH}")
        df = pd.read_excel(EXCEL_PATH)
        
        # 2. Extract Data
        # Mapping: Кафе -> Точка, Предложение -> Выручка
        # Period fixed for now or derived?
        period = "Январь 2026"
        
        export_data = []
        for index, row in df.iterrows():
            outlet = row.get('Кафе')
            revenue = row.get('Предложение')
            comment = "Импорт из Excel"

            if pd.isna(outlet) or pd.isna(revenue):
                continue
            
            # Formatting
            try:
                revenue_float = float(revenue)
                # Google Sheets expects raw numbers for currency formatting to work best, 
                # but we send them as numbers.
            except:
                continue

            export_data.append([period, outlet, revenue_float, comment])

        if not export_data:
            logger.warning("No valid data found to import.")
            return

        logger.info(f"Prepared {len(export_data)} rows for import.")

        # 3. Upload to Google Sheets
        logger.info("Authenticating with Google...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        # Target Tab
        ws = sh.worksheet("2. ПЛАН ПРОДАЖ 📅")
        
        # Clear existing data (keep header)
        # Headers are in A1, data starts A2
        # We find last row or just clear range.
        # But wait, we want to keep the beautiful formatting. 
        # range A2:D1000
        
        # Update logic:
        # A2:D(len)
        
        # Prepare range
        row_count = len(export_data)
        range_name = f"A2:D{1 + row_count}"
        
        logger.info(f"Uploading to {ws.title}...")
        ws.update(range_name=range_name, values=export_data)
        
        print(f"\n✅ DATA IMPORTED: {row_count} rows added to '2. ПЛАН ПРОДАЖ 📅'")

    except Exception as e:
        logger.error(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_sales_plan()
