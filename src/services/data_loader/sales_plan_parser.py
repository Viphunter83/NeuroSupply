
import pandas as pd
from datetime import date
from typing import List, Dict, Optional
from src.db.models import SalesPlan
import uuid
import logging

logger = logging.getLogger(__name__)

class SalesPlanParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self, restaurant_id: uuid.UUID, year: int, month: int) -> List[dict]:
        """
        Parses the Excel file and extracts daily sales plans for a specific month.
        Strategies:
        1. Find a row containing 1, 2, 3... (Days).
        2. Find a row labelled "План" or "Total" or simply below the days.
        """
        try:
            # Read header-less to find structure
            df = pd.read_excel(self.file_path, header=None)
        except Exception as e:
            logger.error(f"Failed to read Excel: {e}")
            return []

        day_row_idx = -1
        plan_values = {}

        # 1. Locate the Days row
        for idx, row in df.iterrows():
            # Check if row has sequence 1, 2, 3...
            # We look for at least 5 consecutive days to be sure
            values = row.dropna().tolist()
            consecutive = 0
            last_val = 0
            
            # Simple heuristic: check if we find 1, 2, 3, 4, 5
            found_sequence = False
            for v in values:
                if isinstance(v, (int, float)):
                    if v == last_val + 1:
                        consecutive += 1
                    else:
                        consecutive = 1
                        last_val = v if v == 1 else 0 # Reset or start if 1
                    
                    if consecutive >= 5:
                        found_sequence = True
                        break
                elif str(v).strip() == '1':
                     last_val = 1
                     consecutive = 1

            if found_sequence:
                day_row_idx = idx
                break
        
        if day_row_idx == -1:
            logger.warning("Could not find row with Days (1..31).")
            return []

        # 2. Extract Data
        # We assume the dates are in this row. We need to find the corresponding columns.
        days_map = {} # day_int -> col_idx
        row_data = df.iloc[day_row_idx]
        
        for col_idx, val in row_data.items():
            try:
                d = int(float(val))
                if 1 <= d <= 31:
                    days_map[d] = col_idx
            except:
                pass

        if not days_map:
             return []

        # 3. Find "Plan" row
        # Usually looking for "Товарооборот" or "Выручка" or "План" in the first few columns
        plan_row_idx = -1
        
        # Search below the day row
        for idx in range(day_row_idx + 1, len(df)):
            row_head = str(df.iloc[idx, 0:5].values).lower() # Check first 5 cols for keyword
            if any(x in row_head for x in ['план', 'выручка', 'товарооборот', 'total', 'sales']):
                plan_row_idx = idx
                break
        
        # Fallback: if not found, maybe it's just the next row?
        if plan_row_idx == -1:
             # Try date_row + 1
             plan_row_idx = day_row_idx + 1
             logger.warning(f"Keyword not found, falling back to row {plan_row_idx}")

        # Extract values
        sales_plans = []
        plan_row = df.iloc[plan_row_idx]

        for d, col in days_map.items():
            try:
                # Handle month length
                try:
                    target_date = date(year, month, d)
                except ValueError:
                    continue # Invalid date (e.g. Feb 30)

                amount = float(plan_row[col])
                
                # Check for NaNs
                if pd.isna(amount): 
                    amount = 0.0
                    
                sales_plans.append({
                    "restaurant_id": restaurant_id,
                    "date": target_date,
                    "amount_rub": amount
                })
            except Exception as e:
                logger.error(f"Error parsing day {d}: {e}")
                continue

        return sales_plans
