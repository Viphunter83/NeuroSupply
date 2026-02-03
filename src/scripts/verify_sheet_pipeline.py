
import asyncio
import uuid
import logging
import sys
import os
from unittest.mock import MagicMock, patch
from decimal import Decimal

# Add project root
sys.path.append(os.getcwd())

from src.scripts.upload_history_to_sheet import analyze_csv
from src.scripts.sync_sheet_to_db import sync_mix_to_db
from src.db.session import async_session_maker
from src.db.models import Restaurant, ProductMix
from sqlalchemy import select, delete

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyPipeline")

# Mock CSV Content
TEST_CSV_PATH = "test_sales.csv"
TEST_CSV_CONTENT = """DishName,DishId,Quantity,Revenue
Soup,uuid-1,10,5000
Salad,uuid-2,5,2500
"""
# Total Rev = 7500
# Soup: 10 qty, 5000 rev. Share = 66.66%. AvgPrice = 500.
# Salad: 5 qty, 2500 rev. Share = 33.33%. AvgPrice = 500.

# Expected Probability (Qty per 1000 RUB)
# Rev per 1000 = 1000
# Soup Share of 1000 = 666.66 RUB. Qty = 666.66 / 500 = 1.3333
# Salad Share of 1000 = 333.33 RUB. Qty = 333.33 / 500 = 0.6666

async def run_verification():
    # 1. Create Dummy CSV
    with open(TEST_CSV_PATH, "w") as f:
        f.write(TEST_CSV_CONTENT)
        
    logger.info("1. Created Test CSV.")

    # 2. Test Analysis (Step 1 Logic)
    logger.info("2. Testing Analysis Logic (CSV -> Sheet Data)...")
    stats = analyze_csv(TEST_CSV_PATH)
    
    # Calculate what would go to sheet
    total_revenue = sum(d['revenue'] for d in stats.values())
    sheet_data = []
    for key, data in stats.items():
        share_percent = float((data["revenue"] / total_revenue) * 100)
        row = {
            "Блюдо": data["dish_name"],
            "Доля в выручке (%)": f"{share_percent:.4f}",
            "Средняя цена (₽)": f"{data['avg_price']:.2f}",
            "iiko_dish_id": data["dish_id"]
        }
        sheet_data.append(row)
        logger.info(f"   Generated Sheet Row: {row}")

    # 3. Test Sync (Step 2 Logic: Sheet -> DB)
    logger.info("3. Testing Sync Logic (Sheet Data -> DB)...")
    
    # Mock SheetsClient in sync_sheet_to_db
    with patch("src.scripts.sync_sheet_to_db.SheetsClient") as MockClient:
        # Construct mock instance
        mock_instance = MockClient.return_value
        mock_instance.fetch_product_mix.return_value = sheet_data
        
        # Setup DB & Restaurant
        async with async_session_maker() as db:
            # Create test restaurant
            r_id = uuid.uuid4()
            rest = Restaurant(
                id=r_id, 
                iiko_id=uuid.uuid4(), # Fix: Provide dummy iiko_id
                name="Test Rest", 
                spreadsheet_id="mock_sheet_id"
            )
            db.add(rest)
            await db.commit()
            
            try:
                # Run Sync
                await sync_mix_to_db(r_id)
                
                # Check Result
                result = await db.execute(select(ProductMix).where(ProductMix.restaurant_id == r_id))
                mixes = result.scalars().all()
                
                logger.info(f"   DB Mixes Found: {len(mixes)}")
                for m in mixes:
                    logger.info(f"   - Dish: {m.iiko_dish_id}, Prob: {m.probability:.4f}")
                    
                    # Validation
                    if "uuid-1" in m.iiko_dish_id: # Soup
                        # Expected: ~1.3333
                        assert 1.33 < m.probability < 1.34, f"Soup Probability mismatch! Got {m.probability}"
                    elif "uuid-2" in m.iiko_dish_id: # Salad
                        # Expected: ~0.6666
                        assert 0.66 < m.probability < 0.67, f"Salad Probability mismatch! Got {m.probability}"
                        
                logger.info("✅ Verification SUCCESS: Probabilities match expectations.")
                
            finally:
                # Cleanup via ORM to handle session state correctly
                # Reload mixes to ensure they are attached or delete manually
                result = await db.execute(select(ProductMix).where(ProductMix.restaurant_id == r_id))
                mixes_to_del = result.scalars().all()
                for m in mixes_to_del:
                    await db.delete(m)
                
                # Now delete parent
                await db.delete(rest)
                await db.commit()
                
                if os.path.exists(TEST_CSV_PATH):
                    os.remove(TEST_CSV_PATH)

if __name__ == "__main__":
    asyncio.run(run_verification())
