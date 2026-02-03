
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

def setup_settings_tab():
    try:
        logger.info("Authenticating...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        # 1. Get or Create Tab
        try:
            ws = sh.worksheet("5. НАСТРОЙКИ ⚙️")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("5. НАСТРОЙКИ ⚙️", rows=100, cols=20)
            
        logger.info("Formatting '5. НАСТРОЙКИ ⚙️' tab...")
        
        ws.clear()
        
        # 2. Define Content
        content = [
            ["⚙️ ЦЕНТР УПРАВЛЕНИЯ (SETTINGS)"], # Row 1
            [""], # Row 2
            ["🏢 ВЫБОР РЕСТОРАНА"], # Row 3
            ["Выберите активный ресторан из списка:"], # Row 4
            ["Активный Ресторан (ID):", "7a416cbc-c318-4aaf-be58-4398e58a4b0d"], # Row 5 (Default Value)
            [""], # Row 6
            ["🧮 ПАРАМЕТРЫ РАСЧЕТА ЗАКАЗА"], # Row 7
            ["Эти настройки влияют на расчет количества продуктов."], # Row 8
            ["Коэффициент Страхового Запаса (Safety Stock):", "1.1"], # Row 9
            ["Буфер 'Дней в пути' (Days in Transit):", "0"], # Row 10
            [""],
            ["📋 СПРАВОЧНИК РЕСТОРАНОВ (Не трогать)"], # Row 12
            ["ID", "Name/Code"], # Row 13
            ["7a416cbc-c318-4aaf-be58-4398e58a4b0d", "FEST"],
            ["02c450f6-9740-43de-80fd-54ea2a20f008", "TPL"],
            ["1495ad6c-bc7e-4a18-95c9-563db20fb42e", "BRT"],
            ["1e599399-4a74-4ca7-beb5-e48a5a5515ec", "PBRK"],
            ["1e9842de-b81c-450b-a020-12cd9d012d54", "MOS"],
            ["37a6cee1-ab33-48da-b461-292ca943279f", "HWD"],
            ["3ae104bd-10a4-4100-938c-b5237eac26af", "FK PITER"],
        ]
        
        ws.update("A1", content)
        
        # 3. Styling using raw batch_update requests for compatibility
        blue_rgb = {"red": 0.29, "green": 0.52, "blue": 0.91}
        yellow_rgb = {"red": 1.0, "green": 0.95, "blue": 0.8}
        
        requests = [
            # A1 Header
            {
                "mergeCells": {
                    "range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 5},
                    "mergeType": "MERGE_ALL"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 5},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": blue_rgb,
                            "horizontalAlignment": "CENTER",
                            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 14, "bold": True}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)"
                }
            },
            # Section Headers (A3, A7, A12)
            {
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 11, "foregroundColor": blue_rgb}}},
                    "fields": "userEnteredFormat(textFormat)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": 6, "endRowIndex": 7, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 11, "foregroundColor": blue_rgb}}},
                    "fields": "userEnteredFormat(textFormat)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": 11, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 11, "foregroundColor": blue_rgb}}},
                    "fields": "userEnteredFormat(textFormat)"
                }
            },
            # Inputs (B5, B9, B10) - Indices are 4, 8, 9 (0-based)
            {
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"backgroundColor": yellow_rgb, "textFormat": {"bold": True}, "horizontalAlignment": "CENTER"}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": 8, "endRowIndex": 10, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {"userEnteredFormat": {"backgroundColor": yellow_rgb, "textFormat": {"bold": True}, "horizontalAlignment": "CENTER"}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            },
            # Col 0 Width
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                    "properties": {"pixelSize": 350},
                    "fields": "pixelSize"
                }
            },
             # Col 1 Width
            {
                "updateDimensionProperties": {
                     "range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                    "properties": {"pixelSize": 250},
                    "fields": "pixelSize"
                }
            }
        ]
        
        # 4. Data Validation for Restaurant ID (B5) using list from A14:A25
        # Note: gspread's batch_update doesn't easily support DV unless we construct the JSON perfectly. 
        # But we can try a simple set_data_validation call again if available on specific cells?
        # Let's rely on manual or just skip DV if complex. 
        # Actually gspread uses `worksheet.add_validation` now? Or `set_data_validation`?
        # Let's try raw request for validation.
        
        dv_request = {
            "setDataValidation": {
                "range": {"sheetId": ws.id, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 1, "endColumnIndex": 2},
                "rule": {
                    "condition": {
                        "type": "ONE_OF_RANGE",
                        "values": [{"userEnteredValue": "='5. НАСТРОЙКИ ⚙️'!A14:A25"}]
                    },
                    "showCustomUi": True,
                    "strict": True
                }
            }
        }
        requests.append(dv_request)
        
        ws.spreadsheet.batch_update({"requests": requests})
        
        print("\n✅ Settings Tab '5. НАСТРОЙКИ ⚙️' configured successfully!")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_settings_tab()
