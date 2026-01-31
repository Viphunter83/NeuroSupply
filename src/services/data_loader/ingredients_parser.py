
import pandas as pd
import re
import uuid
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.db.models.product import Product

logger = logging.getLogger(__name__)

class IngredientsParser:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def parse_package_string(self, text: str) -> tuple[Optional[float], Optional[str]]:
        """
        Parses strings like "1 упаковка - 0,4 кг", "1 коробка - 24 шт", "chai - 0,5 kg"
        Returns: (size, unit)
        """
        if not isinstance(text, str):
            return None, None
            
        text = text.lower().replace(",", ".")
        
        # Pattern: number unit - number unit OR 1 unit - number unit
        # Focus on the LAST number and unit, as that usually defines the total weight/qty
        # Ex: "1 box - 0.4 kg" -> 0.4 kg
        # Ex: "1 box - 24 pcs" -> 24 pcs
        
        # Regex to find the last number-unit pair
        match = re.search(r"-\s*(\d+(?:\.\d+)?)\s*([a-zA-Zа-яА-Я]+)", text)
        if match:
            return float(match.group(1)), match.group(2)
            
        # Fallback: try to find just a number and unit at the end
        match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Zа-яА-Я]+)$", text)
        if match:
            return float(match.group(1)), match.group(2)
            
        return None, None

    def parse(self) -> List[Dict]:
        """
        Reads Excel and returns list of dicts for Product model
        """
        try:
            df = pd.read_excel(self.filepath, header=None)
            products = []
            
            # Start from row 2 (index 2) assuming Row 0 and 1 are garbage/headers based on inspection
            # Row 0: NaN, NaN, ...
            # Row 1: NaN, Наименование... (Header)
            # Row 2: Data...
            
            start_row_index = 0
            # Find header row
            for idx, row in df.iterrows():
                if isinstance(row[1], str) and "Наименование" in str(row[1]):
                    start_row_index = idx + 1
                    break
            
            if start_row_index == 0:
                logger.warning("Header 'Наименование' not found. Trying aggressive start from row 2.")
                start_row_index = 2

            for idx, row in df.iloc[start_row_index:].iterrows():
                name_ru = row[1]
                if pd.isna(name_ru):
                    continue
                    
                name_vn = row[2] if not pd.isna(row[2]) else None
                raw_package = row[4] if not pd.isna(row[4]) else None # Column 4 "Упаковка"
                
                pkg_size, pkg_unit = self.parse_package_string(str(raw_package)) if raw_package else (None, None)
                
                # Deterministic ID based on Name
                product_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(name_ru))
                
                product_data = {
                    "id": product_id,
                    "iiko_id": str(product_id), # Placeholder since no real iiko_id in file
                    "name_ru": str(name_ru).strip(),
                    "name_vn": str(name_vn).strip() if name_vn else None,
                    "unit": pkg_unit if pkg_unit else "шт", # Default unit
                    "package_size": pkg_size,
                    "package_unit": pkg_unit,
                    "category": "Ingredient" # Default category
                }
                products.append(product_data)
                
            return products
            
        except Exception as e:
            logger.error(f"Failed to parse Excel: {e}")
            raise

    async def save_to_db(self, session: Session, products_data: List[Dict]):
        from sqlalchemy import select
        count = 0
        for p_data in products_data:
            # Check exist
            result = await session.execute(select(Product).where(Product.id == p_data["id"]))
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update fields
                existing.name_vn = p_data["name_vn"]
                existing.package_size = p_data["package_size"]
                existing.package_unit = p_data["package_unit"]
            else:
                new_product = Product(**p_data)
                session.add(new_product)
            count += 1
        
        await session.commit()
        logger.info(f"Processed {count} ingredients.")
