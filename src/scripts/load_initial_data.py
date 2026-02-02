
import sys
import os
sys.path.append(os.getcwd())

import asyncio
import logging
import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from src.core.config import settings
from src.db.session import async_session_maker
from src.db.models import Restaurant, Product, SalesPlan
from src.services.iiko.client import IikoClient
from datetime import date, timedelta
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_data():
    logger.info("Starting Data Seeder...")
    
    # 1. Initialize Iiko Client
    iiko = IikoClient()
    token = await iiko.auth()
    if not token:
        logger.error("Failed to auth with Iiko. Exiting.")
        return

    # 2. Seed Restaurant (VDNH)
    org_id = settings.IIKO_ORG_ID
    if not org_id:
        logger.error("IIKO_ORG_ID not set.")
        return

    logger.info(f"Seeding Restaurant: {org_id}")
    async with async_session_maker() as session:
        # Check if exists
        stmt = select(Restaurant).where(Restaurant.iiko_id == org_id)
        result = await session.execute(stmt)
        restaurant = result.scalar_one_or_none()

        if not restaurant:
            # Fetch name from API
            orgs = await iiko.get_organizations()
            org_name = next((o['name'] for o in orgs if o['id'] == org_id), "Unknown Restaurant")
            
            restaurant = Restaurant(
                id=uuid.uuid4(),
                iiko_id=uuid.UUID(org_id),
                name=org_name,
                time_zone="Europe/Moscow",
                settings={}
            )
            session.add(restaurant)
            await session.commit()
            logger.info(f"Created Restaurant: {restaurant.name}")
        else:
            logger.info(f"Restaurant {restaurant.name} already exists.")
        
        restaurant_db_id = restaurant.id

        # 3. Seed Products from Iiko Menu
        logger.info("Fetching Menu from Iiko...")
        menu = await iiko.get_menu(org_id)
        logger.info(f"Got {len(menu.get('products', []))} products from Iiko.")

        # Batch Insert/Update Products
        # We use iiko_id as unique key (it's a string in DB model currently, but let's be careful)
        # Model Product: iiko_id matched by string.

        products_to_upsert = []
        for p in menu.get('products', []):
            products_to_upsert.append({
                "iiko_id": p['id'],
                "name_ru": p['name'],
                "category": p.get('productCategoryId'), # Or name?
                "unit": "шт" # Default, will update from Excel
            })

        # Using upsert logic is cleaner, but for simplicity let's check existence or use merge?
        # Bulk insert/update is better.
        
        # Mapping existing products
        existing_products_stmt = select(Product)
        existing_products_res = await session.execute(existing_products_stmt)
        existing_products = {p.iiko_id: p for p in existing_products_res.scalars().all()}

        count_new = 0
        count_updated = 0

        for p_data in products_to_upsert:
            pid = p_data['iiko_id']
            if pid in existing_products:
                # Update?
                existing = existing_products[pid]
                existing.name_ru = p_data['name_ru']
                if p_data['category']:
                     existing.category = p_data['category']
                count_updated += 1
            else:
                new_p = Product(
                    id=uuid.uuid4(),
                    iiko_id=pid,
                    name_ru=p_data['name_ru'],
                    unit=p_data['unit'],
                    category=p_data['category']
                )
                session.add(new_p)
                count_new += 1
        
        await session.commit()
        logger.info(f"Products sync: {count_new} new, {count_updated} updated.")

        # 4. Enrich from Excel
        excel_path = "data_samples/NEW Ежедневный ВДНХ.xlsx" # Or "Для_кафе..."
        # Try both?
        try:
            logger.info(f"Reading Excel: {excel_path}")
            df = pd.read_excel(excel_path)
            # Expected columns: 'Дата...', 'ЕЖЕДНЕВНЫЙ ЗАКАЗ' (VN Name), ' v19.08 ' (Unit)
            # Clean columns
            # The column names found in inspect: 
            # 'Дата________________________' -> Product Name RU
            # 'ЕЖЕДНЕВНЫЙ ЗАКАЗ' -> Product Name VN
            # ' v19.08 ' -> Unit

            # Rename for easier access
            df.rename(columns={
                'Дата________________________': 'name_ru',
                'ЕЖЕДНЕВНЫЙ ЗАКАЗ': 'name_vn',
                ' v19.08 ': 'unit_excel'
            }, inplace=True)
            
            # Helper to normalize strings
            def clean_str(s):
                return str(s).strip().lower() if pd.notna(s) else ""

            # Reload clean products map
            existing_products_res = await session.execute(select(Product))
            db_products = existing_products_res.scalars().all()
            
            # Map by Name RU (fuzzy or exact?)
            # Iiko names might slightly differ. Let's try exact match (case insensitive).
            
            db_map = {clean_str(p.name_ru): p for p in db_products}
            
            updates = 0
            for _, row in df.iterrows():
                name_ru = clean_str(row.get('name_ru'))
                name_vn = row.get('name_vn')
                unit_excel = row.get('unit_excel')
                
                if name_ru in db_map:
                    product = db_map[name_ru]
                    if pd.notna(name_vn):
                        product.name_vn = str(name_vn)
                    if pd.notna(unit_excel):
                         product.unit = str(unit_excel)
                    updates += 1
                else:
                    # Create new product from Excel
                    new_p = Product(
                        id=uuid.uuid4(),
                        iiko_id=str(uuid.uuid4()), # Generate fake Iiko ID as string
                        name_ru=name_ru,
                        name_vn=str(name_vn) if pd.notna(name_vn) else None,
                        unit=str(unit_excel) if pd.notna(unit_excel) else "шт",
                        category="Uncategorized"
                    )
                    session.add(new_p)
                    # Add to map to avoid duplicates if Excel has same product multiple times
                    db_map[name_ru] = new_p 
                    updates += 1
            
            await session.commit()
            logger.info(f"Enriched {updates} products from Excel.")
            
        except  Exception as e:
            logger.warning(f"Excel enrichment failed or skipped: {e}")


        # 5. Seed Mock Sales Plan (if missing)
        # Create plan for today, tomorrow, day_after
        dates = [date.today(), date.today() + timedelta(days=1), date.today() + timedelta(days=2)]
        for d in dates:
            stmt = select(SalesPlan).where(
                SalesPlan.restaurant_id == restaurant_db_id,
                SalesPlan.date == d
            )
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                # Random amount 40k - 60k
                amount = 50000.0
                plan = SalesPlan(
                    restaurant_id=restaurant_db_id,
                    date=d,
                    amount_rub=amount
                )
                session.add(plan)
        
        await session.commit()
        logger.info("Seeded Mock Sales Plans.")

    await iiko.close()
    logger.info("Seeding Completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
