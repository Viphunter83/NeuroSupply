import logging
import uuid
from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import ProductMix, TechCard, Product, StockBalance

logger = logging.getLogger(__name__)

class CalculationEngineV2:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_needs(self, restaurant_id: uuid.UUID, sales_plan_rub: float) -> List[Dict]:
        """
        Money-to-Ingredient Algorithm:
        1. Sales Plan (RUB) -> 2. Dish Qty (via ProductMix) -> 3. Ingredient Qty (via TechCard)
        """
        logger.info(f"Starting calculation for restaurant {restaurant_id} with plan {sales_plan_rub} RUB")

        # 1. Fetch Product Mix (Sales Statistics)
        stmt_mix = select(ProductMix).where(ProductMix.restaurant_id == restaurant_id)
        result_mix = await self.db.execute(stmt_mix)
        mixes = result_mix.scalars().all()

        if not mixes:
            logger.warning("No ProductMix found. Returning empty list.")
            return []

        # 2. Calculate Dish Quantities
        # Formula: Qty = (Plan / 1000) * Probability
        dish_needs: Dict[str, float] = {}
        for pm in mixes:
            qty = (sales_plan_rub / 1000.0) * float(pm.probability)
            dish_needs[str(pm.iiko_dish_id)] = qty
            # logger.info(f"Dish {pm.iiko_dish_id}: needed {qty:.2f}")

        # 3. Explode to Ingredients via TechCards
        # We need all TechCards for these dishes
        dish_ids = [uuid.UUID(d_id) for d_id in dish_needs.keys()]
        
        stmt_tc = select(TechCard).where(TechCard.iiko_dish_id.in_(dish_ids))
        result_tc = await self.db.execute(stmt_tc)
        tech_cards = result_tc.scalars().all()
        
        ingredient_needs: Dict[uuid.UUID, float] = {}
        
        for tc in tech_cards:
            dish_id_str = str(tc.iiko_dish_id)
            if dish_id_str in dish_needs:
                dish_qty = dish_needs[dish_id_str]
                ingredient_qty = dish_qty * float(tc.gross_amount)
                
                if tc.product_id not in ingredient_needs:
                    ingredient_needs[tc.product_id] = 0.0
                ingredient_needs[tc.product_id] += ingredient_qty

        # 4. Fetch Products details for formatting
        prod_ids = list(ingredient_needs.keys())
        stmt_prods = select(Product).where(Product.id.in_(prod_ids))
        result_prods = await self.db.execute(stmt_prods)
        products_map = {p.id: p for p in result_prods.scalars().all()}

        # 5. Format Result
        # (Optional: Subtract StockBalance here. For MVP/Demo we assume 0 stock or just "Need" = "Order")
        # Let's add simple stock check just to be cool
        stmt_stock = select(StockBalance).where(
            StockBalance.restaurant_id == restaurant_id,
            StockBalance.product_id.in_(prod_ids)
        )
        result_stock = await self.db.execute(stmt_stock)
        stocks = {s.product_id: float(s.amount) for s in result_stock.scalars().all()}

        items = []
        for p_id, qty_needed in ingredient_needs.items():
            if p_id not in products_map:
                continue
                
            product = products_map[p_id]
            current_stock = stocks.get(p_id, 0.0)
            order_qty = max(0.0, qty_needed - current_stock)
            
            # Simple rounding rule
            order_qty = round(order_qty, 2)
            
            if order_qty > 0:
                items.append({
                    "product_id": str(p_id),
                    "product_name": product.name_ru,
                    "product_name_vn": product.name_vn,
                    "unit": product.unit,
                    "quantity": order_qty,
                    "predicted_usage": round(qty_needed, 2),
                    "stock": current_stock,
                    # Add image placeholder
                    "image_url": f"https://placehold.co/150?text={product.name_ru.replace(' ', '+')[:20]}"
                })
        
        logger.info(f"Calculation finished. Generated {len(items)} items.")
        return items
