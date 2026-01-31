
import json
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.db.models.product import Product

logger = logging.getLogger(__name__)

class MenuParser:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def parse(self) -> List[Dict]:
        """
        Reads iiko JSON and returns list of dicts for Product model (Dishes)
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            products_list = data.get("products", [])
            dishes = []
            
            for item in products_list:
                # Filter ONLY Dishes, skip modifiers/goods for now if needed (or keep all)
                # iiko type: "Dish", "Good", "Modifier"
                item_type = item.get("type")
                if item_type not in ["Dish", "Good"]: 
                    continue
                
                # Use iiko ID
                iiko_id = item.get("id")
                name = item.get("name")
                
                dish_data = {
                    "id": None, # Let DB generate UUID or use iiko_id if valid UUID
                    "iiko_id": iiko_id,
                    "name_ru": name,
                    "name_vn": None, # Menu doesn't have VN names usually
                    "unit": item.get("measureUnit", "порц"),
                    "package_size": 1.0, # Dishes are usually 1 portion
                    "package_unit": "порц",
                    "category": "Dish" 
                }
                dishes.append(dish_data)
                
            return dishes
            
        except Exception as e:
            logger.error(f"Failed to parse Menu JSON: {e}")
            raise

    async def save_to_db(self, session: Session, dishes_data: List[Dict]):
        count = 0
        for d_data in dishes_data:
            # Check exist by iiko_id
            stmt = select(Product).where(Product.iiko_id == d_data["iiko_id"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update name just in case
                existing.name_ru = d_data["name_ru"]
            else:
                new_dish = Product(**d_data)
                session.add(new_dish)
            count += 1
        
        await session.commit()
        logger.info(f"Processed {count} dishes.")
