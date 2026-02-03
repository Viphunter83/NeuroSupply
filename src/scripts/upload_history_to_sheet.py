
import asyncio
import csv
import logging
import os
import argparse
import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Any

import sys
# Add project root to path
sys.path.append(os.getcwd())

from src.db.session import async_session_maker
from src.db.models import Restaurant
from src.services.data_loader.sheets_client import SheetsClient
from sqlalchemy import select

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_restaurants(db) -> List[Restaurant]:
    result = await db.execute(select(Restaurant))
    return result.scalars().all()

def analyze_csv(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Reads CSV and calculates stats per dish.
    Returns: { "DishName/ID": { "qty": 10, "revenue": 5000, "avg_price": 500, "id": "..." } }
    """
    stats = {}
    total_rev = Decimal(0)
    
    with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        # Normalize headers
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
        
        has_id = 'dishid' in reader.fieldnames
        has_name = 'dishname' in reader.fieldnames
        
        if not (has_id or has_name):
             logger.error("CSV must have 'DishId' or 'DishName' column.")
             return {}

        for row in reader:
            try:
                qty = Decimal(row.get('quantity', '0').replace(',', '.') or 0)
                rev = Decimal(row.get('revenue', '0').replace(',', '.') or 0)
                
                # Identification preference: Name (for Sheet readability) > ID
                # Actually for unique key we want ID if possible, but for stats grouping let's use Name as primary key for dictionary?
                # The Sheet has "Dish" (Name) and "iiko_dish_id".
                
                dish_name = row.get('dishname', 'Unknown').strip()
                dish_id = row.get('dishid', '').strip()
                
                # Use Name as key for aggregation if available, else ID
                key = dish_name if dish_name else dish_id
                
                if not key:
                    continue

                if key not in stats:
                    stats[key] = {
                        "qty": Decimal(0),
                        "revenue": Decimal(0),
                        "dish_name": dish_name,
                        "dish_id": dish_id
                    }
                
                stats[key]["qty"] += qty
                stats[key]["revenue"] += rev
                total_rev += rev

            except Exception as e:
                logger.warning(f"Skipping row {row}: {e}")
                
    logger.info(f"Analyzed CSV. Total Revenue: {total_rev:,.2f}")
    
    # Enrich with calculated fields
    for key, data in stats.items():
        # Probability = Qty / (TotalRevenue / 1000)
        # i.e. How many items sold per 1000 RUB of total revenue
        if total_rev > 0:
            data["probability"] = float(data["qty"] / (total_rev / Decimal(1000)))
        else:
            data["probability"] = 0.0
            
        # Avg Price
        if data["qty"] > 0:
            data["avg_price"] = float(data["revenue"] / data["qty"])
        else:
            data["avg_price"] = 0.0
            
    return stats

async def main():
    parser = argparse.ArgumentParser(description="Upload Product Mix from CSV to Google Sheets")
    parser.add_argument("--restaurant-id", type=str, help="UUID of the restaurant")
    parser.add_argument("--file", type=str, default="data_samples/sales_history_template.csv", help="Path to CSV file")
    
    args = parser.parse_args()
    
    async with async_session_maker() as db:
        target_rest = None
        if args.restaurant_id:
            target_rest = await db.get(Restaurant, uuid.UUID(args.restaurant_id))
        
        if not target_rest:
            # Interactive or fail
             restaurants = await get_restaurants(db)
             if not restaurants:
                 logger.error("No restaurants found.")
                 return
             
             print("Available Restaurants:")
             for r in restaurants:
                 print(f"- {r.name}: {r.id}")
             
             if not args.restaurant_id:
                 print("Please specify --restaurant-id")
                 return
                 
    if not target_rest.spreadsheet_id:
        logger.error(f"Restaurant {target_rest.name} has no spreadsheet_id configured.")
        return

    # 1. Analyze Data
    logger.info(f"Analyzing {args.file}...")
    stats = analyze_csv(args.file)
    if not stats:
        logger.error("No data found.")
        return

    # 2. Prepare Data for Sheet
    # Headers: ["Точка (Ресторан)", "Блюдо", "Доля в выручке (%)", "Средняя цена (₽)", "iiko_dish_id", "uuid"]
    
    sheet_rows = []
    
    for key, data in stats.items():
        # "Доля в выручке (%)" column name is tricky in the current sheet.
        # In audit it was "Доля в выручке (%)". 
        # But our logic calculates "Qty per 1000 RUB". 
        # If the client expects "Percentage of Revenue" (e.g. 5%), that's different.
        # The 'product_mix' table expects `probability` which we defined as Qty per 1000 RUB in previous conversations.
        # Let's verify what the sheet implies. 
        # Sheet Header: "Доля в выручке (%)". Usually means (DishRevenue / TotalRevenue) * 100.
        # BUT our engine needs Quantity prediction.
        # If we put "Percentage" there, we need to convert it back to Quantity considering Price.
        # Let's stick to our "Probability" (Qty/1000rub) logic but maybe rename column or accept that column name is misleading?
        # OR: We calculate true % share, put it there, and the engine calculates quantity from that?
        # Plan amount (RUB) * Share (%) = Dish Allotted Revenue. 
        # Dish Allotted Revenue / Avg Price = Quantity.
        # This seems more standard for "Share in Revenue".
        
        # Let's calculate BOTH and see.
        # IF the column says "Доля в выручке (%)", it definitively means Revenue Share.
        # Let's switch to Revenue Share logic as it fits the column name perfectly.
        
        # Revenue Share Calculation
        # share = data["revenue"] / total_rev
        pass 

    # RE-EVALUATING LOGIC based on column name "Доля в выручке (%)"
    # Total Rev is calculated in analyze_csv.
    total_revenue = sum(d['revenue'] for d in stats.values())
    
    for key, data in stats.items():
        # Calculate Share %
        if total_revenue > 0:
            share_percent = float((data["revenue"] / total_revenue) * 100)
        else:
            share_percent = 0.0
            
        row = [
            target_rest.name,              # A: Restaurant
            data["dish_name"],             # B: Dish Name
            f"{share_percent:.4f}",        # C: Share % (String formatted)
            f"{data['avg_price']:.2f}",    # D: Avg Price
            data["dish_id"],               # E: iiko_dish_id
            str(uuid.uuid4())              # F: New UUID for this mix entry
        ]
        sheet_rows.append(row)

    # 3. Upload
    logger.info(f"Uploading {len(sheet_rows)} rows to Google Sheet {target_rest.spreadsheet_id}...")
    client = SheetsClient(target_rest.spreadsheet_id)
    client.write_product_mix(sheet_rows)
    logger.info("✅ Upload Complete.")

if __name__ == "__main__":
    asyncio.run(main())
