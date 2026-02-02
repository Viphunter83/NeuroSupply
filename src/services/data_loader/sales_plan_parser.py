
import pandas as pd
from datetime import date
from typing import List, Dict, Optional
import uuid
import logging
import calendar

logger = logging.getLogger(__name__)

class SalesPlanParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self, restaurant_id: uuid.UUID, year: int, month: int, restaurant_code: str = None) -> List[dict]:
        """
        Parses the Google Sheet (Excel export) format "2. ПЛАН ПРОДАЖ".
        Format is Monthly Summary per Restaurant.
        
        Args:
            restaurant_id: The DB ID to assign to the plans.
            restaurant_code: The code in "Точка (Ресторан)" column (e.g. "DNL", "VDNH").
        
        Returns:
            List of daily SalesPlan dicts. Logic: Monthly / DaysInMonth.
        """
        try:
            xl = pd.ExcelFile(self.file_path)
        except Exception as e:
            logger.error(f"Failed to open Excel file: {e}")
            return []

        # 1. Find the Sheet
        target_sheet = None
        for sheet in xl.sheet_names:
            if "ПЛАН" in sheet.upper() and ("ПРОДАЖ" in sheet.upper() or "SALES" in sheet.upper()):
                target_sheet = sheet
                break
        
        if not target_sheet:
            # Fallback to index 2 if exists
            if len(xl.sheet_names) > 2:
                target_sheet = xl.sheet_names[2]
                logger.warning(f"Sheet 'ПЛАН ПРОДАЖ' not found by name. Using index 2: {target_sheet}")
            else:
                logger.error("Could not find Sales Plan sheet.")
                return []

        df = xl.parse(target_sheet)
        
        # 2. Identify Columns
        # Expected: 'Точка (Ресторан)', 'Прогноз Выручки (₽)', 'Период (Месяц/Неделя)'
        col_map = {}
        for col in df.columns:
            c = str(col).lower()
            if "точка" in c or "ресторан" in c:
                col_map['code'] = col
            elif "выруч" in c or "прогноз" in c or "amount" in c:
                col_map['amount'] = col
            elif "период" in c:
                col_map['period'] = col
        
        if 'code' not in col_map or 'amount' not in col_map:
            logger.error(f"Required columns not found in {target_sheet}. Found: {df.columns}")
            return []

        # 3. Find Row
        target_amount = 0.0
        found = False
        
        # Helper to match date (simple str matching for now "Январь 2026")
        # We need to map (year, month) -> "Январь 2026"
        month_names = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        target_period_str = f"{month_names[month]} {year}" # e.g. "Январь 2026"
        
        for idx, row in df.iterrows():
            # Check Period
            if 'period' in col_map:
                per = str(row[col_map['period']]).strip()
                # Fuzzy match or exact?
                # The file has "Январь 2026".
                if target_period_str.lower() not in per.lower():
                    continue

            # Check Code
            r_code = str(row[col_map['code']]).strip()
            
            # If restaurant_code provided, match it
            if restaurant_code:
                if r_code.lower() == restaurant_code.lower():
                    target_amount = float(row[col_map['amount']])
                    found = True
                    break
            else:
                # If not provided, maybe match by ID? Impossible. 
                # Fallback: Just take the first one? Or error?
                # Let's log warning and take the first one for testing purposes.
                logger.warning(f"No restaurant_code provided. Using first row for {r_code}")
                try:
                    target_amount = float(row[col_map['amount']])
                    found = True
                    break
                except:
                    continue

        if not found:
            logger.warning(f"No plan found for code '{restaurant_code}' in period '{target_period_str}'")
            return []

        # 4. Generate Daily Plans
        # Logic: Uniform distribution
        _, days_in_month = calendar.monthrange(year, month)
        daily_amount = target_amount / days_in_month
        
        sales_plans = []
        for d in range(1, days_in_month + 1):
            sales_plans.append({
                "restaurant_id": restaurant_id,
                "date": date(year, month, d),
                "amount_rub": round(daily_amount, 2)
            })
            
        logger.info(f"Generated {len(sales_plans)} daily plans of {daily_amount:.2f} RUB for {restaurant_code}")
        return sales_plans
