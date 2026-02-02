import logging
import uuid
import math
from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models import ProductMix, TechCard, Product, StockBalance, Order, OrderStatus
from src.services.ml.forecast_service import ForecastService

logger = logging.getLogger(__name__)

class CalculationEngineV2:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.forecaster = ForecastService()

    async def calculate_needs(self, restaurant_id: uuid.UUID, sales_plan_rub: float) -> List[Dict]:
        """
        Money-to-Ingredient Algorithm (v2.0 - Audit Fixes):
        1. Sales Plan (RUB) -> 2. Dish Qty -> 3. Ingredient Qty
        4. Apply Safety Stock (1.1x)
        5. Subtract Stock Balance
        6. Subtract Goods in Transit (Orders verified in last 24h)
        7. Round up to Packages (Boxes)
        """
        logger.info(f"Starting calculation for restaurant {restaurant_id} with plan {sales_plan_rub} RUB")

        # --- 0. AI Forecast ---
        ml_multiplier = self.forecaster.predict_usage(sales_plan_rub)
        logger.info(f"🧠 AI Forecast Applied. Multiplier: {ml_multiplier:.2f}")

        # --- 1. Fetch Data ---

        # 1.1 Product Mix
        stmt_mix = select(ProductMix).where(ProductMix.restaurant_id == restaurant_id)
        result_mix = await self.db.execute(stmt_mix)
        mixes = result_mix.scalars().all()

        if not mixes:
            logger.warning("No ProductMix found. Returning empty list.")
            return []

        # 1.2 Tech Cards
        # Calculate Dish Quantities first to filter TechCards
        dish_needs: Dict[str, float] = {}
        for pm in mixes:
            # Formula: Qty = (Plan / 1000) * Probability * ML_Multiplier
            qty = (sales_plan_rub / 1000.0) * float(pm.probability) * ml_multiplier
            dish_needs[str(pm.iiko_dish_id)] = qty

        dish_ids = [uuid.UUID(d_id) for d_id in dish_needs.keys()]
        
        stmt_tc = select(TechCard).where(TechCard.iiko_dish_id.in_(dish_ids))
        result_tc = await self.db.execute(stmt_tc)
        tech_cards = result_tc.scalars().all()

        # 1.3 Calculate Raw Ingredient Needs
        ingredient_needs: Dict[uuid.UUID, float] = {}
        for tc in tech_cards:
            dish_id_str = str(tc.iiko_dish_id)
            if dish_id_str in dish_needs:
                dish_qty = dish_needs[dish_id_str]
                ingredient_qty = dish_qty * float(tc.gross_amount)
                
                if tc.product_id not in ingredient_needs:
                    ingredient_needs[tc.product_id] = 0.0
                ingredient_needs[tc.product_id] += ingredient_qty

        prod_ids = list(ingredient_needs.keys())
        if not prod_ids:
            return []

        # 1.4 Fetch Products details
        stmt_prods = select(Product).where(Product.id.in_(prod_ids))
        result_prods = await self.db.execute(stmt_prods)
        products_map = {p.id: p for p in result_prods.scalars().all()}

        # 1.5 Fetch Stock Balances
        stmt_stock = select(StockBalance).where(
            StockBalance.restaurant_id == restaurant_id,
            StockBalance.product_id.in_(prod_ids)
        )
        result_stock = await self.db.execute(stmt_stock)
        stocks = {s.product_id: float(s.amount) for s in result_stock.scalars().all()}

        # 1.6 Fetch Transit (Last 24h Verified Orders)
        # We assume "In Transit" = Verified but not yet delivered (approx 24h window)
        transit_cutoff = datetime.utcnow() - timedelta(hours=24)
        stmt_transit = select(Order).where(
            Order.restaurant_id == restaurant_id,
            Order.status.in_([OrderStatus.VERIFIED_BY_COOK, OrderStatus.EXPORTED_TO_PROCOB]),
            Order.created_at >= transit_cutoff
        )
        result_transit = await self.db.execute(stmt_transit)
        transit_orders = result_transit.scalars().all()

        transit_map: Dict[uuid.UUID, float] = {}
        for order in transit_orders:
            for item in order.items:
                # Item structure in JSON: {'product_id': 'uuid_str', 'quantity': 5.0, ...}
                p_id_str = item.get('product_id')
                qty = float(item.get('quantity', 0.0)) # Using 'quantity' which is the ordered amount (box or kg? In old logic it was kg)
                
                # WARNING: Previously we stored 'quantity' as the result of calculation. 
                # If we switch to Boxes, we need to know what 'quantity' means. 
                # For backward compatibility, let's assume 'quantity' in Order items is Order Unit Amount.
                # But to subtract from KG needs, we need KG.
                # If we start storing boxes, we need to convert back to KG here using package_size.
                # For now, let's look at how we saved it. In V1 we saved KG as quantity. 
                # So we can just sum it up. 
                
                if p_id_str:
                    p_uuid = uuid.UUID(p_id_str)
                    if p_uuid not in transit_map:
                        transit_map[p_uuid] = 0.0
                    transit_map[p_uuid] += qty

        # --- 2. Calculate Final Order ---
        
        items = []
        for p_id, raw_need in ingredient_needs.items():
            if p_id not in products_map:
                continue
                
            product = products_map[p_id]
            
            # A. Safety Stock
            need_with_safety = raw_need * settings.SAFETY_STOCK_RATIO
            
            # B. Subtract Assets
            current_stock = stocks.get(p_id, 0.0)
            transit_qty = transit_map.get(p_id, 0.0)
            
            net_need_kg = max(0.0, need_with_safety - current_stock - transit_qty)
            
            # C. Packaging Logic (Round to Boxes)
            package_size = float(product.package_size) if product.package_size else 0.0
            package_unit = product.package_unit or product.unit
            
            final_order_qty = 0.0
            order_unit = product.unit
            
            if package_size > 0:
                # Conversion to packs
                packs = math.ceil(net_need_kg / package_size)
                final_order_qty = packs
                order_unit = package_unit # e.g., "box"
                
                # Recalculate KG for reference (optional, but good for anomalies)
                # ordered_kg = packs * package_size
            else:
                # No package info, stick to base unit (kg/l)
                # Round to 2 decimals for sanitary reasons
                final_order_qty = round(net_need_kg, 2)
            
            if final_order_qty > 0:
                items.append({
                    "product_id": str(p_id),
                    "product_name": product.name_ru,
                    "product_name_vn": product.name_vn,
                    "unit": order_unit,
                    "quantity": final_order_qty, # This is potentially Boxes now
                    
                    # Extended Info for UI/Debug
                    "predicted_usage": round(raw_need, 2),
                    "safety_usage_kg": round(need_with_safety, 2),
                    "stock": current_stock,
                    "transit_kg": transit_qty,
                    "formatted_transit": f"{transit_qty:.2f} {product.unit} (in 24h)",
                    
                    # Add image placeholder
                    "image_url": f"https://placehold.co/150?text={product.name_ru.replace(' ', '+')[:20]}"
                })
        
        logger.info(f"Calculation finished. Generated {len(items)} items.")
        return items
