
import asyncio
import logging
import os
import sys
import uuid
from typing import Dict, List, Optional
from decimal import Decimal

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select, delete
from src.db.session import async_session_maker
from src.db.models import Restaurant, ProductMix
from src.services.data_loader.sheets_client import SheetsClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_mix_to_db(restaurant_id: uuid.UUID):
    async with async_session_maker() as db:
        # 1. Get Restaurant & Sheet ID
        restaurant = await db.get(Restaurant, restaurant_id)
        if not restaurant or not restaurant.spreadsheet_id:
            logger.error(f"Restaurant {restaurant_id} not found or missing spreadsheet_id.")
            return

        logger.info(f"Syncing Mix for {restaurant.name} from sheet {restaurant.spreadsheet_id}...")
        
        # 2. Fetch Data from Sheet
        client = SheetsClient(restaurant.spreadsheet_id)
        data = client.fetch_product_mix() # List of dicts
        
        if not data:
            logger.warning("No data found in '3. ПРОДУКТОВЫЙ МИКС 📊'.")
            return

        # 3. Process & Convert
        # Sheet Columns: "Точка (Ресторан)", "Блюдо", "Доля в выручке (%)", "Средняя цена (₽)", "iiko_dish_id", "uuid"
        
        new_mixes = []
        
        for row in data:
            try:
                # Parse basics
                dish_name = str(row.get("Блюдо", "")).strip()
                iiko_id = str(row.get("iiko_dish_id", "")).strip()
                
                # Parse Share % and Price
                share_str = str(row.get("Доля в выручке (%)", "0")).replace(",", ".").replace("%", "").strip()
                price_str = str(row.get("Средняя цена (₽)", "0")).replace(",", ".").replace("₽", "").replace("\xa0", "").strip()
                
                share_percent = float(share_str) if share_str else 0.0
                avg_price = float(price_str) if price_str else 0.0
                
                if avg_price <= 0:
                    # Avoid division by zero
                    # If revenue share > 0 but price is 0, we can't calculate quantity.
                    if share_percent > 0:
                        logger.warning(f"Skipping {dish_name}: Share {share_percent}% but Price is 0. Cannot calc quantity.")
                    continue
                    
                # Formula: Probability (Qty per 1000 RUB) = (Share% * 10) / AvgPrice
                # Explanation:
                # Share% = 5 (means 5%)
                # Rev per 1000 = 1000 * 0.05 = 50
                # Qty = 50 / AvgPrice
                # 50 = 5 * 10
                
                probability = (share_percent * 10) / avg_price
                
                if probability > 0:
                    mix = ProductMix(
                        restaurant_id=restaurant.id,
                        iiko_dish_id=dish_name, # Use explicit dish name to map with EmpiricalRecipe seamlessly
                        probability=probability,
                        # We could store share/price in DB too if we expanded the model, but for now just probability
                    )
                    new_mixes.append(mix)
                    
            except Exception as e:
                logger.error(f"Error parsing row {row}: {e}")

        # 4. Update DB
        if new_mixes:
            # Delete old mix for this restaurant
            logger.info(f"Deleting existing mix for restaurant {restaurant.id}...")
            await db.execute(delete(ProductMix).where(ProductMix.restaurant_id == restaurant.id))
            
            # Insert new
            logger.info(f"Inserting {len(new_mixes)} new mix entries...")
            db.add_all(new_mixes)
            await db.commit()
            logger.info("✅ Database updated successfully.")
        else:
            logger.warning("No valid mix entries found to insert.")


async def sync_all_restaurants():
    """
    Finds all restaurants in DB with spreadsheet_id and syncs them.
    """
    logger.info("🚀 Starting global sync for all restaurants...")
    async with async_session_maker() as db:
        stmt = select(Restaurant).where(Restaurant.spreadsheet_id != None)
        result = await db.execute(stmt)
        restaurants = result.scalars().all()
        
        if not restaurants:
            logger.warning("No restaurants found with spreadsheet_id in DB.")
            return

        for rest in restaurants:
            try:
                logger.info(f"--- [Sync] {rest.name} ---")
                await sync_mix_to_db(rest.id)
            except Exception as e:
                logger.error(f"Failed to sync {rest.name}: {e}")
    
    logger.info("✅ Global sync completed.")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sync Product Mix from Sheet to DB")
    parser.add_argument("--restaurant-id", type=str, help="UUID of the restaurant (optional)")
    parser.add_argument("--all", action="store_true", help="Sync all restaurants")
    
    args = parser.parse_args()
    
    if args.all:
        await sync_all_restaurants()
    elif args.restaurant_id:
        try:
            r_id = uuid.UUID(args.restaurant_id)
            await sync_mix_to_db(r_id)
        except ValueError:
            logger.error("Invalid UUID format.")
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
