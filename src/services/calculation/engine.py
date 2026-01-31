
import math
import logging
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.db.models.product import Product, TechCard

logger = logging.getLogger(__name__)

class CalculationEngine:
    def __init__(self, session: Session):
        self.session = session

    async def calculate_requirements(self, sales_plan: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Calculates ingredient requirements based on Sales Plan (Dish ID -> Qty).
        Returns list of ingredients with 'required_amount' and 'order_amount' (packages).
        """
        requirements = {} # product_id -> {product: Obj, total_gross: float}

        # 1. Iterate Sales Plan
        for dish_id, plan_qty in sales_plan.items():
            # Get Tech Cards for this dish
            stmt = select(TechCard).where(TechCard.iiko_dish_id == dish_id)
            result = await self.session.execute(stmt)
            tech_cards = result.scalars().all()
            
            if not tech_cards:
                logger.warning(f"No recipe found for Dish ID {dish_id}")
                continue
                
            for tc in tech_cards:
                ing_id = tc.product_id
                gross = float(tc.gross_amount)
                total_needed = gross * plan_qty
                
                if ing_id not in requirements:
                    # Get Ingredient info (lazy load or eager load earlier)
                    ing_stmt = select(Product).where(Product.id == ing_id)
                    ing_res = await self.session.execute(ing_stmt)
                    ingredient = ing_res.scalar_one_or_none()
                    
                    if ingredient:
                        requirements[ing_id] = {
                            "product": ingredient,
                            "total_gross": 0.0
                        }
                
                if ing_id in requirements:
                    requirements[ing_id]["total_gross"] += total_needed

        # 2. Rounding Logic (Order Generation)
        order_list = []
        for ing_id, data in requirements.items():
            product = data["product"]
            total_gross = data["total_gross"]
            pkg_size = float(product.package_size) if product.package_size else None
            
            order_qty = 0
            comment = ""
            
            if pkg_size and pkg_size > 0:
                # Round Up to nearest package
                packages_needed = math.ceil(total_gross / pkg_size)
                order_qty = packages_needed
                order_amount_kg = packages_needed * pkg_size
                comment = f"Need {total_gross:.3f} {product.unit} -> {packages_needed} x {pkg_size} {product.package_unit}"
            else:
                # Fallback if no package size: just order exact amount (or treat as 'pcs')
                order_qty = math.ceil(total_gross)
                comment = f"Need {total_gross:.3f} {product.unit} (No Pkg info)"

            order_list.append({
                "ingredient_name": product.name_ru,
                "required_amount": total_gross,
                "unit": product.unit,
                "package_size": pkg_size,
                "order_qty": order_qty,
                "order_unit": product.package_unit or "шт",
                "comment": comment
            })
            
        return order_list
