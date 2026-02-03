import sys
import os
import asyncio
import logging
from typing import Dict, Optional

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import engine
from src.db.models import Product, Restaurant
from src.services.data_loader.sheets_client import SheetsClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_sheets():
    logger.info("🚀 Starting Sheets Migration (Adding System IDs)...")
    
    sheets = SheetsClient(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
    
    # Setup DB
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Load All Products Map: {NameRU -> ID}
        logger.info("Fetching products from DB...")
        result = await session.execute(select(Product))
        products = result.scalars().all()
        products_map: Dict[str, str] = {p.name_ru.strip().lower(): str(p.id) for p in products}
        logger.info(f"Loaded {len(products_map)} products from DB.")

        # --- 1. Migrate Tech Cards ("1. ТЕХКАРТЫ 🍲") ---
        logger.info("Processing Tab: 1. ТЕХКАРТЫ 🍲")
        
        # Ensure Headers
        tc_dish_col = sheets.ensure_header("1. ТЕХКАРТЫ 🍲", "Dish_ID", row_index=1)
        tc_ing_col = sheets.ensure_header("1. ТЕХКАРТЫ 🍲", "Ingredient_ID", row_index=1)
        
        # Fetch Raw Data
        tc_data = sheets.fetch_tech_cards() # List of dicts
        
        dish_ids_to_write = []
        ing_ids_to_write = []
        
        for row in tc_data:
            dish_name = str(row.get("Блюдо / Полуфабрикат", "")).strip()
            ing_name = str(row.get("Ингредиент", "")).strip()
            
            # Lookup Dish
            d_id = products_map.get(dish_name.lower(), "")
            dish_ids_to_write.append(d_id)
            if not d_id and dish_name:
                logger.warning(f"⚠️ Dish not found in DB: '{dish_name}'")
                
            # Lookup Ingredient
            i_id = products_map.get(ing_name.lower(), "")
            ing_ids_to_write.append(i_id)
            if not i_id and ing_name:
                logger.warning(f"⚠️ Ingredient not found in DB: '{ing_name}'")

        # Write Back
        if dish_ids_to_write:
            logger.info(f"Writing {len(dish_ids_to_write)} Dish IDs...")
            sheets.update_column_data("1. ТЕХКАРТЫ 🍲", tc_dish_col, dish_ids_to_write, start_row=2)
            
        if ing_ids_to_write:
            logger.info(f"Writing {len(ing_ids_to_write)} Ingredient IDs...")
            sheets.update_column_data("1. ТЕХКАРТЫ 🍲", tc_ing_col, ing_ids_to_write, start_row=2)


        # --- 2. Migrate Product Mix ("3. ПРОДУКТОВЫЙ МИКС 📊") ---
        logger.info("Processing Tab: 3. ПРОДУКТОВЫЙ МИКС 📊")
        
        # Ensure Header
        pm_dish_col = sheets.ensure_header("3. ПРОДУКТОВЫЙ МИКС 📊", "Dish_ID", row_index=1)
        
        # Fetch Data
        pm_data = sheets.fetch_product_mix()
        
        pm_ids_to_write = []
        
        for row in pm_data:
            dish_name = str(row.get("Блюдо", "")).strip()
            
            d_id = products_map.get(dish_name.lower(), "")
            pm_ids_to_write.append(d_id)
            
            if not d_id and dish_name:
                logger.warning(f"⚠️ Mix Dish not found in DB: '{dish_name}'")
                
        # Write Back
        if pm_ids_to_write:
            logger.info(f"Writing {len(pm_ids_to_write)} Mix IDs...")
            sheets.update_column_data("3. ПРОДУКТОВЫЙ МИКС 📊", pm_dish_col, pm_ids_to_write, start_row=2)

    logger.info("✅ Migration Completed! Check Google Sheet.")

if __name__ == "__main__":
    try:
        asyncio.run(migrate_sheets())
    except KeyboardInterrupt:
        pass
