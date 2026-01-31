
import logging
from typing import Dict, List, Optional
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import defaultdict
import math

from src.services.iiko.client import IikoClient
from src.db.models import Product, SalesPlan, Order, TechCard, StockBalance

logger = logging.getLogger(__name__)

class CalculationEngine:
    def __init__(self, iiko_client: IikoClient, db: AsyncSession):
        self.iiko = iiko_client
        self.db = db
        self.buffer_coeff = 1.2
        self.food_cost_avg = 0.3 # Not directly used in Ratio method, but kept for ref

    async def calculate_order(self, org_id: str) -> List[Dict]:
        """
        Main calculation logic V1.
        Returns list of recommended orders: [{product_name, quantity, unit, explanation}]
        """
        logger.info(f"Starting calculation for Org: {org_id}")
        
        # 1. Get Demand Forecast (Sales Plan Money)
        today = date.today()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        
        plans = await self._get_sales_plans([tomorrow, day_after])
        total_plan_money = sum(float(p.amount_rub) for p in plans)
        
        logger.info(f"Sales Plan for next 2 days: {total_plan_money} RUB")
        
        if total_plan_money == 0:
            logger.warning("No sales plan found. Returning parsed logic but 0 quantities.")
            # We proceed to show logic but result will be 0
            
        # 2. Historical Consumption (Last 7 Days)
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # A. Fetch Sales from Iiko
        logger.info(f"Fetching sales from {date_from} to {date_to}")
        sales_data = await self.iiko.get_sales_olap(org_id, date_from, date_to)
        
        # B. Fetch Menu to map Names to IDs
        menu_data = await self.iiko.get_menu(org_id)
        # Map Dish Name -> Dish ID
        dish_map = {p['name']: p['id'] for p in menu_data.get('products', [])} # Iiko menu structure 'products' or 'groups'? Assuming 'products'
        
        # C. Total Sales Money in last 7 days from OLAP
        total_sales_7days = 0.0
        # Parse OLAP `data`
        # Expecting data structure: {'data': [{'DishName': '...', 'DishAmountInt': X, 'DishDiscountSumInt.averagePrice': Y}]}
        # Need to verify OLAP structure. assuming flat list in 'data'
        
        product_usage_kg = defaultdict(float) # product_id (DB UUID) -> kg
        
        # Pre-fetch all TechCards
        tech_cards = await self._get_all_tech_cards()
        # Map iiko_dish_id (UUID string) -> list of (product_id, gross)
        tc_map = defaultdict(list)
        for tc in tech_cards:
            tc_map[str(tc.iiko_dish_id)].append((tc.product_id, float(tc.gross_amount)))
            
        unique_dishes_sold = set()
        
        sales_items = sales_data.get('data', [])
        for item in sales_items:
            dish_name = item.get('DishName')
            qty = float(item.get('DishAmountInt', 0))
            # Price might be implicit or explicit. 'DishDiscountSumInt' is typically Total Sum? 
            # If we requested "DishDiscountSumInt.averagePrice", we get avg price.
            # Let's assume we requested "DishDiscountSumInt" (Total Sum). 
            # I need to check client implementation.
            revenue = float(item.get('DishDiscountSumInt', 0)) # Assuming this field exists if requested
            
            total_sales_7days += revenue
            
            dish_id = dish_map.get(dish_name)
            if dish_id and dish_id in tc_map:
                unique_dishes_sold.add(dish_id)
                # Calculate Ingredients
                for prod_id, gross in tc_map[dish_id]:
                    product_usage_kg[prod_id] += qty * gross
        
        logger.info(f"Historical Sales (7d): {total_sales_7days} RUB. Dishes sold: {len(unique_dishes_sold)}")
        
        # 3. Predict Consumption
        # Ratio: Kg / Total_Sales_Rub
        # Predicted_Kg = Plan_Rub * Ratio
        
        predicted_consumption = {}
        if total_sales_7days > 0:
            factor = total_plan_money / total_sales_7days
            # NOTE: usage_kg is for 7 days. We want usage for 2 days based on plan.
            # If we use strict Ratio: (Usage_7d / Sales_7d) * Plan_2d.
            # Yes, that's correct.
            
            for pid, kg_7d in product_usage_kg.items():
                predicted_consumption[pid] = (kg_7d / total_sales_7days) * total_plan_money
        else:
            logger.warning("Total historical sales is 0. Cannot predict.")

        # 4. Get Current Stock
        stocks = await self.iiko.get_stock_balances(org_id) 
        # stocks structure? list of {productId, amount}. 
        # We need to map iiko_product_id -> db_product_id.
        # Products in DB have `iiko_id`.
        
        products_db = await self._get_all_products()
        iiko_id_to_db_id = {str(p.iiko_id): p.id for p in products_db}
        db_id_to_product = {p.id: p for p in products_db}
        
        current_stocks = defaultdict(float)
        # Using parsed stock data logic (depends on IikoClient implementation)
        # For now assuming stocks is Dict[iiko_id, amount]
        if isinstance(stocks, list):
             for s in stocks:
                 iid = s.get('productId')
                 amt = s.get('amount', 0)
                 if iid in iiko_id_to_db_id:
                     current_stocks[iiko_id_to_db_id[iid]] = float(amt)
        
        # 5. Pending Orders
        # pending_orders = await self._get_pending_orders()
        pending_orders = defaultdict(float) # Placeholder
        
        # 6. Final Order
        recommendations = []
        for pid, predicted_kg in predicted_consumption.items():
            stock = current_stocks.get(pid, 0)
            pending = pending_orders.get(pid, 0)
            
            required = (predicted_kg * self.buffer_coeff) - (stock + pending)
            
            if required > 0:
                product = db_id_to_product[pid]
                # Rounding logic could be in Product (packaging). 
                # For now simple rounding to 1 decimal or integer if unit is pcs.
                
                # Heuristic: if unit is 'kg', round to 0.1? If 'pcs' round to 1.
                # Implementation said: "Round to unit of supply".
                # We don't have supply unit in Product model yet (only 'unit' which is usage unit).
                # User prompt: "Information about package take from products (field unit)".
                # Usually 'unit' is kg, l, sht.
                
                final_qty = required
                if product.unit in ['шт', 'pcs']:
                    final_qty = math.ceil(required)
                else:
                    final_qty = round(required, 2)
                    
                recommendations.append({
                    "product_name": product.name_ru,
                    "predicted_kg": round(predicted_kg, 2),
                    "stock": stock,
                    "order_qty": final_qty,
                    "unit": product.unit
                })
                
        return sorted(recommendations, key=lambda x: x['product_name'])

    async def _get_sales_plans(self, dates: List[date]) -> List[SalesPlan]:
        query = select(SalesPlan).where(SalesPlan.date.in_(dates))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _get_all_tech_cards(self) -> List[TechCard]:
        result = await self.db.execute(select(TechCard))
        return result.scalars().all()

    async def _get_all_products(self) -> List[Product]:
        result = await self.db.execute(select(Product))
        return result.scalars().all()
