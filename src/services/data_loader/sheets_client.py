import os
import json
import gspread
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import settings

class SheetsClient:
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    def __init__(self):
        key_path = settings.GOOGLE_SHEETS_CREDENTIALS_PATH
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Service account key not found at {key_path}")
            
        self.creds = Credentials.from_service_account_file(key_path, scopes=self.SCOPE)
        self.client = gspread.authorize(self.creds)
        self.sheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_tech_cards(self) -> List[Dict[str, Any]]:
        """
        Fetches Tech Cards from '1. ТЕХКАРТЫ 🍲' tab.
        Expected columns: Dish Name, Product Name, Netto (kg/unit)
        """
        sheet = self.client.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet("1. ТЕХКАРТЫ 🍲")
        return worksheet.get_all_records()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_product_mix(self) -> List[Dict[str, Any]]:
        """
        Fetches Product Mix from '3. ПРОДУКТОВЫЙ МИКС 📊' tab.
        Expected columns: iiko_dish_id, Dish Name, Probability (qty per 1000 rub)
        """
        sheet = self.client.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet("3. ПРОДУКТОВЫЙ МИКС 📊")
        return worksheet.get_all_records()

    def clear_worksheet(self, tab_name: str):
        """Clears all content from a specific worksheet."""
        sheet = self.client.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet(tab_name)
        worksheet.clear()

    def update_worksheet(self, tab_name: str, data: List[List[Any]]):
        """Updates a worksheet with new data (list of lists)."""
        sheet = self.client.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet(tab_name)
        worksheet.update(data)

    def get_monthly_plan_target(self) -> dict:
        """
        Reads the Monthly Plan header from '2. ПЛАН ПРОДАЖ 📅'.
        Assumes structure: 
        Row 1: ["Месяц", "Сумма Плана"]
        Row 2: ["Январь 2026", 2050219]
        """
        sheet = self.client.open_by_key(self.sheet_id)
        ws = sheet.worksheet("2. ПЛАН ПРОДАЖ 📅")
        
        # Read header cells
        month = ws.acell('A2').value
        target_str = ws.acell('B2').value
        
        try:
            target = float(str(target_str).replace(",", "").replace("₽", "").strip())
        except:
            target = 0.0
            
        return {"month": month, "target": target}

    def update_daily_forecast(self, rows: List[List[Any]]):
        """
        Updates the daily forecast table in '2. ПЛАН ПРОДАЖ 📅'.
        Writes starting from Row 4.
        """
        sheet = self.client.open_by_key(self.sheet_id)
        ws = sheet.worksheet("2. ПЛАН ПРОДАЖ 📅")
        
        # Header for table
        header = ["Дата", "День недели", "Сумма (План)"]
        
        # Write Header at A4
        ws.update("A4:C4", [header])
        
        # Write Data from A5
        if rows:
            end_row = 4 + len(rows)
            range_name = f"A5:C{end_row}"
            ws.update(range_name, rows)

    def get_plan_for_date(self, date_str: str) -> float:
        """
        Finds the plan amount for a specific date (DD.MM.YYYY).
        """
        sheet = self.client.open_by_key(self.sheet_id)
        ws = sheet.worksheet("2. ПЛАН ПРОДАЖ 📅")
        
        # Get all records starting from row 4
        # expected headers in row 4
        records = ws.get_all_records(head=4) 
        
        for row in records:
            if row.get("Дата") == date_str:
                try:
                    val = str(row.get("Сумма (План)"))
                    return float(val.replace(",", "").replace("₽", "").strip())
                except:
                    return 0.0
        return 0.0

    def get_or_create_worksheet(self, title: str):
        """Gets a worksheet by title, or creates it if it doesn't exist."""
        sheet = self.client.open_by_key(self.sheet_id)
        try:
            return sheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            return sheet.add_worksheet(title=title, rows=100, cols=20)

    def get_active_restaurant_id(self) -> str:
        """
        Reads the Active Restaurant ID from 'НАСТРОЙКИ ⚙️' tab, Cell B2.
        Fallback to env var IIKO_ORG_ID if missing or empty.
        """
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            ws = sheet.worksheet("НАСТРОЙКИ ⚙️")
            val = ws.acell('B2').value
            if val and len(val.strip()) > 10: # Simple validation for UUID-like string
                return val.strip()
        except:
            pass
        
        # Fallback
        return settings.IIKO_ORG_ID

    def get_active_restaurant_name(self) -> str:
        """
        Resolves the Active Restaurant Name based on the ID in 'НАСТРОЙКИ ⚙️'.
        Scans values in Columns D (Name) and E (ID).
        """
        active_id = self.get_active_restaurant_id()
        if not active_id:
            return "Unknown"
            
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            ws = sheet.worksheet("НАСТРОЙКИ ⚙️")
            
            # Get all values from D and E
            # Assuming list starts at row 5 or so, just fetch all
            data = ws.get_all_values()
            
            for row in data:
                # Check bounds
                if len(row) < 5: 
                    continue
                
                # Col D is index 3, Col E is index 4
                r_name = row[3].strip()
                r_id = row[4].strip()
                
                if r_id == active_id:
                    return r_name
        except:
            pass
            
        return "Unknown"

    def get_monthly_plan_target(self, restaurant_name: str = None) -> dict:
        """
        Reads the Monthly Plan header from '2. ПЛАН ПРОДАЖ 📅'.
        Logic:
        1. Access '2. ПЛАН ПРОДАЖ 📅'.
        2. Scan Rows 2-10.
        3. If 'restaurant_name' is found in Col B (index 1), use that row's Target (Col C, index 2).
        4. Fallback: Use Row 2 default.
        """
        sheet = self.client.open_by_key(self.sheet_id)
        ws = sheet.worksheet("2. ПЛАН ПРОДАЖ 📅")
        
        # Fetch Top 10 rows
        rows = ws.get_values("A1:E10")
        
        target_row = None
        
        # 1. Try to find specific row for restaurant
        if restaurant_name:
            for r in rows:
                if len(r) > 1 and restaurant_name.lower() in str(r[1]).lower():
                    target_row = r
                    break
        
        # 2. Fallback to Row 2 (Index 1) if not found or no name provided
        if not target_row and len(rows) > 1:
            target_row = rows[1] # Row 2
            
        if not target_row:
             return {"month": "Unknown", "target": 0.0}

        try:
            month = target_row[0]
            
            # Smart Detection of Target Column
            # Check Column B (Index 1)
            col_b = target_row[1] if len(target_row) > 1 else ""
            clean_b = str(col_b).replace(",", "").replace("₽", "").replace("\xa0", "").strip()
            
            is_b_numeric = False
            try:
                float(clean_b)
                is_b_numeric = True
            except:
                pass
                
            if is_b_numeric:
                # Case 1: Col B is the Target (e.g. General Row: [Month, 3000000, ...])
                target = float(clean_b)
            else:
                # Case 2: Col B is Name (e.g. [Month, ARTL, 4000000]) -> Target is Col C (Index 2)
                col_c = target_row[2] if len(target_row) > 2 else "0"
                target = float(str(col_c).replace(",", "").replace("₽", "").replace("\xa0", "").strip())
                
        except:
            target = 0.0
            
        return {"month": month, "target": target}

    def find_column_index(self, worksheet, header_name: str, header_row: int = 1) -> int:
        """Finds usage of a column by header name (1-based index). Returns -1 if not found."""
        try:
            headers = worksheet.row_values(header_row)
            if header_name in headers:
                return headers.index(header_name) + 1
            return -1
        except:
            return -1

    def ensure_header(self, tab_name: str, header_name: str, row_index: int = 1) -> int:
        """
        Checks if header exists. If not, adds it to the first empty column.
        Returns the 1-based column index of the header.
        """
        sheet = self.client.open_by_key(self.sheet_id)
        ws = sheet.worksheet(tab_name)
        
        col_idx = self.find_column_index(ws, header_name, row_index)
        if col_idx != -1:
            return col_idx
            
        # Add new column
        headers = ws.row_values(row_index)
        new_col_idx = len(headers) + 1
        ws.update_cell(row_index, new_col_idx, header_name)
        return new_col_idx

    def update_column_data(self, tab_name: str, col_idx: int, data: List[str], start_row: int = 2):
        """
        Updates a specific column with data starting from start_row.
        Data is a list of strings.
        """
        sheet = self.client.open_by_key(self.sheet_id)
        ws = sheet.worksheet(tab_name)
        
        # Prepare range
        if not data:
            return
            
        # Transform flat list to list of lists for gspread: [['id1'], ['id2']]
        cell_values = [[str(x)] for x in data]
        
        end_row = start_row + len(data) - 1
        
        from gspread.utils import rowcol_to_a1
        range_start = rowcol_to_a1(start_row, col_idx)
        range_end = rowcol_to_a1(end_row, col_idx)
        
        ws.update(f"{range_start}:{range_end}", cell_values)
