import sys
import os
sys.path.append(os.getcwd())

import asyncio
import uuid
import logging
from typing import Dict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.session import engine
from src.db.models import Restaurant, Product, ProductMix, TechCard, StockBalance
from src.services.data_loader.sheets_client import SheetsClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# from src.db.models import Restaurant, Product, ProductMix, TechCard, StockBalance
# from src.core.config import settings

# REST_ID = uuid.UUID("f2c046ab-4068-4794-b6e1-e41045f9ea31") # REMOVED

async def seed_logic_data():
    logger.info("Starting Seed Logic from Sheets...")
    
    sheets = SheetsClient(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
    
    # 1. Fetch Data from Sheets
    logger.info("Fetching data from Google Sheets...")
    try:
        tech_cards_raw = sheets.fetch_tech_cards() # List of dicts
        mix_data_raw = sheets.fetch_product_mix() # List of dicts
    except Exception as e:
        logger.error(f"Failed to fetch from sheets: {e}")
        return

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            # 2. Verify Restaurant
            # Dynamic ID from Sheets
            org_id = sheets.get_active_restaurant_id()
            if not org_id:
                logger.error("No Active Restaurant ID found.")
                return
            
            # Check if exists by iiko_id
            stmt = select(Restaurant).where(Restaurant.iiko_id == org_id)
            res = await session.execute(stmt)
            restaurant = res.scalar_one_or_none()
            
            if not restaurant:
                # Fallback: get first restaurant
                logger.warning(f"Restaurant with IIKO_ID {org_id} not found. Trying any restaurant.")
                res = await session.execute(select(Restaurant).limit(1))
                restaurant = res.scalar_one_or_none()
                
            if not restaurant:
                logger.error("No restaurant found in DB. Run load_initial_data.py first.")
                return

            logger.info(f"Using Restaurant: {restaurant.name} ({restaurant.id})")

            # Optional: Clear existing Logic Data (TechCards, ProductMix) to avoid dups
            # Be careful with Products if they are referenced elsewhere, but for dev it is fine.
            logger.info("Clearing old TechCards and ProductMix...")
            await session.execute(delete(TechCard))
            await session.execute(delete(ProductMix))
            # valid to clear stock too? Maybe.
            # await session.execute(delete(StockBalance))

            # 3. Process Products (Ingredients & Dishes)
            # Map: {Name -> Product} AND {ID -> Product}
            product_map_by_name: Dict[str, Product] = {}
            product_map_by_id: Dict[str, Product] = {}

            # Helper to get or create product
            async def get_or_create_product(name: str, category: str, unit: str = "kg", sheet_id: str = None):
                # 1. Try Lookup by Sheet ID (Strongest Match)
                if sheet_id and len(sheet_id) > 10: # Basic UUID check
                    stmt = select(Product).where(Product.id == uuid.UUID(sheet_id))
                    res = await session.execute(stmt)
                    existing = res.scalar_one_or_none()
                    
                    if existing:
                        # Sync Name if changed
                        if existing.name_ru != name:
                            logger.info(f"🔄 Renaming Product {existing.id}: {existing.name_ru} -> {name}")
                            existing.name_ru = name
                            # session.add(existing) # Already tracked
                        
                        product_map_by_id[str(existing.id)] = existing
                        product_map_by_name[name] = existing
                        return existing

                # 2. Try Lookup by Name (Legacy/Fallback)
                if name in product_map_by_name:
                    return product_map_by_name[name]
                
                # Check DB by Name
                stmt = select(Product).where(Product.name_ru == name)
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()
                
                if existing:
                    product_map_by_name[name] = existing
                    product_map_by_id[str(existing.id)] = existing
                    return existing
                
                # 3. Create New
                new_id = uuid.uuid4()
                # If sheet provided a valid ID but we didn't find it (Deleted in DB?), should we reuse it?
                # Safer to generate new to avoid conflicts, or trust Sheet? 
                # Let's trust Sheet ID if it looks like a valid UUID, to restore "Ghost" products?
                # No, for safety generate NEW if not found, unless we want to do a "Restore" feature.
                # Let's keep it simple: New Product = New ID.
                
                new_prod = Product(
                    id=new_id,
                    iiko_id=str(new_id),
                    name_ru=name,
                    unit=unit,
                    category=category
                )
                session.add(new_prod)
                product_map_by_name[name] = new_prod
                product_map_by_id[str(new_id)] = new_prod
                return new_prod

            # 3.1 Process Ingredients from Tech Cards
            # Columns: 'Блюдо / Полуфабрикат', 'Ингредиент', ... 'Dish_ID', 'Ingredient_ID'
            logger.info("Processing Ingredients...")
            for row in tech_cards_raw:
                ing_name = str(row.get("Ингредиент", "")).strip()
                ing_id = str(row.get("Ingredient_ID", "")).strip() # New Column
                unit = row.get("Ед. изм.", "kg")
                
                if ing_name:
                    await get_or_create_product(ing_name, "Ingredient", unit, sheet_id=ing_id)

            # 3.2 Process Dishes from Tech Cards & Mix
            logger.info("Processing Dishes...")
            unique_dishes = {} # Name -> ID map to deduplicate
            
            for row in tech_cards_raw:
                d_name = str(row.get("Блюдо / Полуфабрикат", "")).strip()
                d_id = str(row.get("Dish_ID", "")).strip()
                if d_name:
                    unique_dishes[d_name] = d_id
            
            for row in mix_data_raw:
                d_name = str(row.get("Блюдо", "")).strip()
                d_id = str(row.get("Dish_ID", "")).strip()
                if d_name:
                    # Prefer ID from Mix if missing in TC (unlikely but possible)
                    if d_name not in unique_dishes or not unique_dishes[d_name]:
                        unique_dishes[d_name] = d_id

            for d_name, d_id in unique_dishes.items():
                await get_or_create_product(d_name, "Dish", "portion", sheet_id=d_id)

            # Force session flush
            await session.flush()
            
            # 4. Create Tech Cards
            logger.info("Seeding Tech Cards...")
            tc_count = 0
            for row in tech_cards_raw:
                dish_name = str(row.get("Блюдо / Полуфабрикат", "")).strip()
                ing_name = str(row.get("Ингредиент", "")).strip()
                gross = row.get("Брутто (Кол-во)")
                
                # ID Lookups can be done via name map since we pre-loaded everything
                # CAUTION: If we have 2 products "Sugar" and "Sugar" (duplicate names allowed?), map is risky.
                # But our get_or_create enforces uniqueness by name if ID matches failed. 
                # So Name is still secondary key.
                
                if not (dish_name and ing_name and gross):
                    continue
                    
                dish = product_map_by_name.get(dish_name)
                ing = product_map_by_name.get(ing_name)
                
                if dish and ing:
                    try:
                        qty = float(str(gross).replace(",", "."))
                    except:
                        qty = 0.0
                        
                    tc = TechCard(
                        id=uuid.uuid4(),
                        iiko_dish_id=dish.id, # Using internal UUID here as primary link
                        product_id=ing.id,
                        gross_amount=qty
                    )
                    session.add(tc)
                    tc_count += 1
            
            # 5. Create Product Mix
            logger.info("Seeding Product Mix...")
            pm_count = 0
            for row in mix_data_raw:
                dish_name = row.get("Блюдо")
                prob_str = row.get("Доля в выручке (%)")
                
                if not dish_name:
                    continue
                
                dish = product_map_by_name.get(dish_name)
                if dish:
                    try:
                        clean_str = str(prob_str).replace(",", ".").replace("%", "").strip()
                        val = float(clean_str)
                        # Heuristic: if > 1.0, treat as percentage (e.g. 14.29 -> 0.1429)
                        # if <= 1.0, treat as fraction (e.g. 0.1429 -> 0.1429)
                        if val > 1.0:
                            share_fraction = val / 100.0
                        else:
                            share_fraction = val
                    except:
                        share_fraction = 0.0
                    
                    # Convert Share Fraction + Price -> Qty Factor (Qty per 1000 RUB)
                    # Formula: Qty = (1000 * ShareFraction) / Price
                    price_str = row.get("Средняя цена (₽)", "0")
                    try:
                        price = float(str(price_str).replace(",", ".").replace("₽", "").strip())
                    except:
                        price = 0.0
                    
                    if price > 0:
                        qty_factor = (1000 * share_fraction) / price
                    else:
                        qty_factor = 0.0

                    pm = ProductMix(
                        id=uuid.uuid4(),
                        restaurant_id=restaurant.id,
                        iiko_dish_id=str(dish.id), # Linking to our Dish UUID
                        probability=qty_factor # Storing Qty Factor for Engine
                    )
                    session.add(pm)
                    pm_count += 1

            logger.info(f"Seeding Complete. TechCards: {tc_count}, ProductMix: {pm_count}")
            
    await engine.dispose()
    logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(seed_logic_data())
