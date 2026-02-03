
import asyncio
import csv
import logging
import os
import uuid
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session_maker
from src.db.models import Restaurant, ProductMix

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_restaurants(db: AsyncSession) -> List[Restaurant]:
    result = await db.execute(select(Restaurant))
    return result.scalars().all()

async def train_from_csv(file_path: str, restaurant_id: uuid.UUID):
    logger.info(f"Reading sales data from {file_path}...")
    
    total_revenue = Decimal(0)
    dish_stats: Dict[str, Decimal] = {} # Key: DishIdentifier (ID or Name), Value: Quantity

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return

    with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Normalize headers (strip BOM, lower case)
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
        
        required_cols = {'quantity', 'revenue'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            logger.error(f"CSV missing required columns. Found: {reader.fieldnames}. Required: quantity, revenue, dishname (or dishid)")
            return

        has_id = 'dishid' in reader.fieldnames
        has_name = 'dishname' in reader.fieldnames
        
        if not (has_id or has_name):
             logger.error("CSV must have 'DishId' or 'DishName' column.")
             return

        for row in reader:
            try:
                qty = Decimal(row['quantity'].replace(',', '.') or 0)
                rev = Decimal(row['revenue'].replace(',', '.') or 0)
                
                # Identification preference: ID > Name
                identifier = row.get('dishid') if has_id and row.get('dishid') else row.get('dishname')
                
                if not identifier:
                    continue

                total_revenue += rev
                dish_stats[identifier] = dish_stats.get(identifier, Decimal(0)) + qty

            except Exception as e:
                logger.warning(f"Skipping row {row}: {e}")

    logger.info(f"Total Revenue processed: {total_revenue:,.2f}")
    
    if total_revenue == 0:
        logger.error("Total revenue is 0, cannot calculate probabilities.")
        return

    # Calculate Probabilities (Qty per 1000 RUB)
    # Prob = Qty / (TotalRevenue / 1000)
    revenue_thousands = total_revenue / Decimal(1000)
    
    new_mixes = []
    
    for identifier, qty in dish_stats.items():
        probability = float(qty / revenue_thousands)
        
        # Simple heuristic: if probability is super low (< 0.0001), maybe ignore? 
        # But let's keep all.
        
        new_mixes.append(ProductMix(
            restaurant_id=restaurant_id,
            iiko_dish_id=str(identifier),
            probability=probability
        ))

    logger.info(f"Generated {len(new_mixes)} Product Mix entries.")

    async with async_session_maker() as db:
        # Clear existing mix for this restaurant? 
        # Only if we are doing a full retraining. Let's assume yes.
        logger.info(f"Clearing old ProductMix for restaurant {restaurant_id}...")
        await db.execute(delete(ProductMix).where(ProductMix.restaurant_id == restaurant_id))
        
        logger.info("Inserting new mix...")
        db.add_all(new_mixes)
        await db.commit()
        logger.info("✅ Product Mix updated successfully.")


import argparse

async def main():
    parser = argparse.ArgumentParser(description="Train Product Mix from CSV")
    parser.add_argument("--restaurant-id", type=str, help="UUID of the restaurant")
    parser.add_argument("--file", type=str, default="data_samples/sales_history_template.csv", help="Path to CSV file")
    
    args = parser.parse_args()
    
    async with async_session_maker() as db:
        if not args.restaurant_id:
            # Interactive mode fallback or just list
            restaurants = await get_restaurants(db)
            if not restaurants:
                logger.error("No restaurants found.")
                return
            
            print("Available Restaurants:")
            for r in restaurants:
                print(f"- {r.name}: {r.id}")
            
            print("\nPlease provide --restaurant-id <UUID> to run.")
            return

        try:
            r_id = uuid.UUID(args.restaurant_id)
        except ValueError:
            logger.error("Invalid UUID format.")
            return
            
        await train_from_csv(args.file, r_id)

if __name__ == "__main__":
    asyncio.run(main())

