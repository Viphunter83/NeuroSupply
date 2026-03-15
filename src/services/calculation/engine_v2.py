import logging
import uuid
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models import ProductMix, EmpiricalRecipe, Product, StockBalance, Order, OrderStatus
from src.services.ml.forecast_service import ForecastService

logger = logging.getLogger(__name__)

class CalculationEngineV2:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.forecaster = ForecastService()

    async def calculate_needs(self, restaurant_id: uuid.UUID, sales_plan_rub: float, safety_stock: float = None, days_in_transit: int = 0) -> tuple[List[Dict], List[Dict]]:
        """
        Money-to-Ingredient Algorithm (v2.0 - Audit Fixes):
        1. Sales Plan (RUB) -> 2. Dish Qty -> 3. Ingredient Qty
        4. Apply Safety Stock (Dynamic or Default 1.1x)
        5. Subtract Stock Balance
        6. Subtract Goods in Transit (Orders verified in last 24h + days_in_transit buffer)
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
            return [], []

        # 1.2 Tech Cards
        # Calculate Dish Quantities first to filter TechCards
        dish_needs: Dict[str, float] = {}
        
        def clean_dish_name(name: str) -> str:
            # Remove common iiko suffixes like " (доставка)", " (самовывоз)"
            return name.replace(" (доставка)", "").replace("(доставка)", "").strip()

        for pm in mixes:
            # Formula: Qty = (Plan / 1000) * Probability * ML_Multiplier
            qty = (sales_plan_rub / 1000.0) * float(pm.probability) * ml_multiplier
            raw_id = str(pm.iiko_dish_id)
            dish_needs[raw_id] = qty
            
            # Add cleaned name to needs if it's different
            cleaned = clean_dish_name(raw_id)
            if cleaned != raw_id:
                dish_needs[cleaned] = dish_needs.get(cleaned, 0.0) + qty

        dish_ids = []
        dish_names = []
        for d_id_str in dish_needs.keys():
            try:
                dish_ids.append(uuid.UUID(d_id_str))
            except ValueError:
                dish_names.append(d_id_str)
        
        # Filter recipes at SQL level
        conditions = []
        if dish_ids:
            conditions.append(EmpiricalRecipe.dish_id.in_(dish_ids))
        if dish_names:
            conditions.append(EmpiricalRecipe.dish_name.in_(dish_names))
        
        if conditions:
            from sqlalchemy import or_
            stmt_recipe = select(EmpiricalRecipe).where(or_(*conditions))
            result_recipe = await self.db.execute(stmt_recipe)
            empirical_recipes = result_recipe.scalars().all()
        else:
            empirical_recipes = []

        # 1.3 Calculate Raw Ingredient Needs
        ingredient_needs: Dict[uuid.UUID, float] = {}
        unmapped_needs: Dict[str, float] = {}

        for recipe in empirical_recipes:
            dish_key = str(recipe.dish_id) if recipe.dish_id and str(recipe.dish_id) in dish_needs else recipe.dish_name
            if dish_key in dish_needs:
                dish_qty = dish_needs[dish_key]
                ingredient_qty = dish_qty * float(recipe.yield_rate)
                
                if recipe.product_id:
                    if recipe.product_id not in ingredient_needs:
                        ingredient_needs[recipe.product_id] = 0.0
                    ingredient_needs[recipe.product_id] += ingredient_qty
                else:
                    if recipe.ingredient_name not in unmapped_needs:
                        unmapped_needs[recipe.ingredient_name] = 0.0
                    unmapped_needs[recipe.ingredient_name] += ingredient_qty

        prod_ids = list(ingredient_needs.keys())
        if not prod_ids and not unmapped_needs:
            return [], []

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
        last_verified_cutoff = datetime.now(timezone.utc) - timedelta(hours=24 + (days_in_transit * 24))
        stmt_transit = select(Order).where(
            Order.restaurant_id == restaurant_id,
            Order.status.in_([OrderStatus.VERIFIED_BY_COOK, OrderStatus.EXPORTED_TO_PROCOB]),
            Order.created_at >= last_verified_cutoff
        )
        result_transit = await self.db.execute(stmt_transit)
        transit_orders = result_transit.scalars().all()

        transit_map: Dict[uuid.UUID, float] = {}
        for order in transit_orders:
            for item in order.items:
                p_id_str = item.get('product_id')
                # Item structure in JSON: {'product_id': 'uuid_str', 'quantity': 5.0, ...}
                if p_id_str:
                    p_uuid = uuid.UUID(p_id_str)
                    if p_uuid not in transit_map:
                        transit_map[p_uuid] = 0.0
                    
                    # Use 'quantity_kg' if available, fallback to 'quantity'
                    q_kg = float(item.get('quantity_kg', item.get('quantity', 0.0)))
                    transit_map[p_uuid] += q_kg

        # --- 2. Calculate Final Order ---
        
        # Determine effective Safety Stock
        ss_ratio = safety_stock if safety_stock is not None else settings.SAFETY_STOCK_RATIO
        
        items = []
        for p_id, raw_need in ingredient_needs.items():
            if p_id not in products_map:
                continue
                
            product = products_map[p_id]
            
            # A. Safety Stock
            need_with_safety = raw_need * ss_ratio
            
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
                # Calculate what this order represents in KG for future transit checks
                ordered_kg = final_order_qty * package_size if package_size > 0 else final_order_qty

                items.append({
                    "product_id": str(p_id),
                    "product_name": product.name_ru,
                    "product_name_vn": product.name_vn,
                    "unit": order_unit,
                    "quantity": final_order_qty, # Boxes or KG
                    "quantity_kg": round(ordered_kg, 4), # Always KG
                    
                    # Extended Info for UI/Debug
                    "predicted_usage": round(raw_need, 2),
                    "safety_usage_kg": round(need_with_safety, 2),
                    "stock": current_stock,
                    "transit_kg": transit_qty,
                    "formatted_transit": f"{transit_qty:.2f} {product.unit} (in transit)",
                    
                    # Add image placeholder
                    "image_url": f"https://placehold.co/150?text={product.name_ru.replace(' ', '+')[:20]}"
                })
        
        # Append unmapped needs directly (useful for tracking things not in DB but existing in iiko)
        for ingr_name, raw_need in unmapped_needs.items():
            need_with_safety = raw_need * ss_ratio
            items.append({
                "product_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, ingr_name)),  # Deterministic ID for same ingredient
                "product_name": f"{ingr_name} (Не привязан)",
                "product_name_vn": "",
                "unit": "кг",
                "quantity": round(need_with_safety, 2),
                "quantity_kg": round(need_with_safety, 4),
                "predicted_usage": round(raw_need, 2),
                "safety_usage_kg": round(need_with_safety, 2),
                "stock": 0.0,
                "transit_kg": 0.0,
                "formatted_transit": "0.0 кг",
                "image_url": "https://placehold.co/150?text=Unmapped"
            })
            
        logger.info(f"Calculation finished. Generated {len(items)} items.")
        
        # New Return Structure: (Items, DishBreakdown)
        # DishBreakdown: List[Dict] with details about what dishes contributed to the plan
        dish_breakdown = []
        for d_id_str, qty in dish_needs.items():
            # Find dish name if possible. We have tech_cards but not direct Dish objects here efficiently.
            # We can map from iiko_dish_id to name via TechCard or Mix.
            # Mix has 'iiko_dish_id' but maybe no name. TechCard has iiko_dish_id.
            # For visualization, we simply pass ID and Qty.
            # Better: Fetch Dish names in Step 1.2 or 1.1 if available.
            
            dish_breakdown.append({
                "iiko_dish_id": d_id_str,
                "quantity": round(qty, 2),
                "plan_revenue": round((qty / ml_multiplier) * 1000 if ml_multiplier > 0 else 0, 2) # Reverse engineering approximate revenue part? Or just use probability.
            })

        return items, dish_breakdown
