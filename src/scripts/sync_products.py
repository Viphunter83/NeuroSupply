"""
Sync product nomenclature from iiko resto API → products table.
Goal: Ensure all products found in stock/sales have a record in the DB with correct resto iiko_id.

Strategy:
1. Fetch all products from iiko resto.
2. Fetch existing products from DB.
3. Match by name (normalized) or existing iiko_id.
4. Update iiko_id to resto UUID and update metadata (unit, category).
5. Insert new products that are not in DB.
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional

from sqlalchemy import select
from src.core.config import settings
from src.services.iiko.client import IikoClient
from src.db.session import async_session_maker
from src.db.models.product import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common iiko unit UUIDs to names mapping
UNIT_MAP = {
    '7ba81c3a-8de5-8f9d-fb9f-e39efcbc57cc': 'кг',
    'cd19b5ea-1b32-a6e5-1df7-5d2784a0549a': 'шт',
    '6040d92d-e286-f4f9-a613-ed0e6fd241e1': 'л',
    '69859c74-db72-b006-cba5-326cf6f4fc6e': 'порц',
    '09760c59-96a2-438e-a021-93c21ad5680b': 'гр',
}

import re

def normalize_name(name: str) -> str:
    if not name: return ""
    return name.lower().strip().replace("  ", " ")

def parse_package_size(name: str) -> tuple[Optional[float], Optional[str]]:
    """
    Extracts package size and unit from name.
    Example: "Lợi 0.54 kg" -> (0.54, "кг")
    Example: "Banh bao 6 шт" -> (6.0, "шт")
    """
    # Pattern: Digit (maybe comma) + space? + unit
    pattern = r"(\d+[.,]?\d*)\s*(кг|kg|гр|gr|g|шт|pcs|порц)"
    match = re.search(pattern, name.lower())
    if not match:
        return None, None
        
    val_str = match.group(1).replace(",", ".")
    unit_str = match.group(2)
    
    try:
        val = float(val_str)
        # Normalize unit
        if unit_str in ['кг', 'kg']: unit = 'кг'
        elif unit_str in ['гр', 'gr', 'g']: 
            val = val / 1000.0 # Convert to base unit kg
            unit = 'кг'
        elif unit_str in ['шт', 'pcs']: unit = 'шт'
        else: unit = unit_str
        
        return val, unit
    except ValueError:
        return None, None

async def sync_products():
    client = IikoClient()
    try:
        logger.info("Fetching nomenclature from iiko resto API...")
        resto_products = await client.get_products_list_resto()
        logger.info(f"Received {len(resto_products)} items from iiko.")

        async with async_session_maker() as session:
            # Load existing products
            stmt = select(Product)
            res = await session.execute(stmt)
            db_products = res.scalars().all()
            
            # Index by name_ru and by iiko_id
            db_by_name = {normalize_name(p.name_ru): p for p in db_products if p.name_ru}
            db_by_id = {str(p.iiko_id).lower(): p for p in db_products if p.iiko_id}
            
            updated_count = 0
            inserted_count = 0
            
            for rp in resto_products:
                rp_id = str(rp.get('id', '')).lower()
                rp_name = rp.get('name', '')
                rp_type = rp.get('type', '')
                rp_unit_id = rp.get('mainUnit', '')
                
                # We only care about products that can have stock or be sold
                if rp_type not in ['GOODS', 'PREPARED', 'DISH']:
                    continue

                unit_name = UNIT_MAP.get(rp_unit_id, 'шт') # Default to 'шт' if unknown
                
                # Parse package info
                pkg_size, pkg_unit = parse_package_size(rp_name)
                
                # Check if it exists in DB
                product = db_by_id.get(rp_id) or db_by_name.get(normalize_name(rp_name))
                
                if product:
                    # Update existing
                    product.iiko_id = rp_id # Ensure it has the resto ID
                    product.name_ru = rp_name
                    product.unit = unit_name
                    if pkg_size:
                        product.package_size = pkg_size
                        product.package_unit = pkg_unit
                    # preserve name_vn and other fields if they exist
                    updated_count += 1
                else:
                    # Create new
                    new_prod = Product(
                        iiko_id=rp_id,
                        name_ru=rp_name,
                        unit=unit_name,
                        category=str(rp.get('category', '')),
                        package_size=pkg_size,
                        package_unit=pkg_unit
                    )
                    session.add(new_prod)
                    inserted_count += 1

            await session.commit()
            logger.info(f"✅ Product sync completed: {updated_count} updated, {inserted_count} inserted.")

    except Exception as e:
        logger.error(f"❌ Product sync failed: {e}", exc_info=True)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(sync_products())
