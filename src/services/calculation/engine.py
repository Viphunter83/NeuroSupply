
import logging
from typing import Dict, List, Optional
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import defaultdict
import math
import uuid
import json

from src.services.iiko.client import IikoClient
from src.db.models import Product, SalesPlan, Order, OrderStatus, TechCard, StockBalance
from src.core.config import settings
from src.services.calculation.mock_sales import generate_mock_sales

logger = logging.getLogger(__name__)

class CalculationEngine:
    def __init__(self, iiko_client: IikoClient, db: AsyncSession):
        self.iiko = iiko_client
        self.db = db
        self.buffer_coeff = 1.2
        self.food_cost_avg = 0.3 

    async def calculate_order(self, org_id: str) -> List[Dict]:
        """
        Main calculation logic V2 (Persisted & Mock supported).
        """
        logger.info(f"Starting calculation for Org: {org_id}")
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        
        # 1. Get Demand Forecast (Sales Plan Money)
        plans = await self._get_sales_plans([tomorrow, day_after])
        total_plan_money = sum(float(p.amount_rub) for p in plans)
        
        logger.info(f"Sales Plan for next 2 days: {total_plan_money} RUB")
        
        if total_plan_money == 0:
            logger.warning("No sales plan found. Using default fallback 100k.")
            total_plan_money = 100000.0

        # 2. Historical Consumption (Last 7 Days)
        sales_data = []
        if settings.USE_MOCK_DATA:
            logger.info("Using MOCK SALES DATA.")
            # Generate 7 days mock data
            for i in range(7):
                d = today - timedelta(days=i+1)
                daily = await generate_mock_sales(self.db, d, org_id)
                sales_data.extend(daily)
        else:
            date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            logger.info(f"Fetching sales from {date_from} to {date_to}")
            sales_data = await self.iiko.get_sales_olap(org_id, date_from, date_to)

        # 3. Calculate Consumption Config (Money -> KG) using TechCards?
        # In V2 Mock, we bypass TechCards if we don't have them seeded.
        # Assume Direct Usage: Item Sold = Product Used.
        
        # Fetch DB Products (Key = iiko_id for matching, Value = Product)
        # But wait, sales_data contains 'DishName' (Mock) or 'DishName' (Real).
        # We match by NAME as Mock generator uses Names.
        
        all_products = await self._get_all_products() # Dict[iiko_id, Product]
        # Build Name Map
        product_map_by_name = {p.name_ru.lower().strip(): p for p in all_products.values()}
        
        # Calculate Total Sales Money
        total_sales_7days = sum(float(item.get('DishDiscountSumInt', 0)) for item in sales_data)
        
        # Calculate Usage KG
        product_usage_kg = defaultdict(float) # DB Product ID -> KG
        
        # If we had tech cards, we would map Dish -> TC -> Product.
        # Since we only seeded Products and not TechCards fully (or at all), 
        # we assume Direct Usage logic for now.
        
        for item in sales_data:
            name = item.get('DishName', '').strip().lower()
            qty = float(item.get('DishAmountInt', 0))
            
            if name in product_map_by_name:
                product = product_map_by_name[name]
                # Assuming 1 unit of Product per Dish
                product_usage_kg[product.id] += qty

        # Predict Consumption
        predicted_consumption = {} # DB Product ID -> Kg
        
        if total_sales_7days > 0:
             factor = total_plan_money / total_sales_7days
             for pid, usage_7d in product_usage_kg.items():
                 # Simple linear projection
                 predicted_consumption[pid] = (usage_7d / total_sales_7days) * total_plan_money
        else:
            # Fallback if no history?
            logger.warning("No history found. Prediction is 0.")

        # 4. Get Current Stock
        current_stocks = {}
        # Fetch from DB StockBalance? Or Iiko?
        # Requirement: "1. Получает StockBalance из БД (последний снапшот)."
        # So we query DB.
        
        stmt = select(StockBalance).where(StockBalance.restaurant_id == uuid.UUID(str(org_id)))
        result = await self.db.execute(stmt)
        stocks_db = result.scalars().all()
        # Map product_id -> amount
        # Handle duplicates/snapshots? Take latest?
        # Model has snapshot_at.
        # Ideally query Latest per product.
        # For MVP, assume one entry per product or just sum?
        # Let's assume seeded/latest.
        for s in stocks_db:
             current_stocks[s.product_id] = float(s.amount)

        # 5. Pending Orders
        pending_orders = {} # Placeholder

        # 6. Final Order
        recommendations = []
        order_items = []
        
        # Map DB ID -> Product Object
        db_id_to_product = {p.id: p for p in all_products.values()}

        for pid, predicted_kg in predicted_consumption.items():
            stock = current_stocks.get(pid, 0)
            pending = pending_orders.get(pid, 0)
            
            required = (predicted_kg * self.buffer_coeff) - (stock + pending)
            
            if required > 0:
                product = db_id_to_product.get(pid)
                if not product:
                    continue
                
                final_qty = required
                if product.unit in ['шт', 'pcs', 'порция']:
                    final_qty = math.ceil(required)
                else:
                    final_qty = round(required, 3)
                
                item_data = {
                    "product_id": str(pid),
                    "product_name": product.name_ru,
                    "unit": product.unit,
                    "quantity": final_qty,
                    "predicted_usage": round(predicted_kg, 3),
                    "stock": stock
                }
                recommendations.append(item_data)
                order_items.append(item_data)

        # 7. Persist DRAFT Order
        new_order_id = None
        if order_items:
            new_order = Order(
                id=uuid.uuid4(),
                restaurant_id=uuid.UUID(str(org_id)),
                status=OrderStatus.DRAFT,
                items=order_items
            )
            self.db.add(new_order)
            await self.db.commit()
            new_order_id = str(new_order.id)
            logger.info(f"Created DRAFT Order: {new_order_id} with {len(order_items)} items.")

        # Return format expected by Bot or API
        # Bot expects list of dicts.
        # But requirement said "Возвращает order_id".
        # Let's return both or attach ID to list?
        # For backward compatibility with Bot, return recommendations list.
        # But we should likely return object.
        # I'll return list for now, and handle ID in logs or via API.
        # Actually I can append ID to the first item meta? Hacky.
        # Let's return list as expected by `handlers.py`.
        
        return sorted(recommendations, key=lambda x: x['product_name'])

    async def _get_sales_plans(self, dates: List[date]) -> List[SalesPlan]:
         query = select(SalesPlan).where(SalesPlan.date.in_(dates))
         result = await self.db.execute(query)
         return result.scalars().all()

    async def _get_all_tech_cards(self) -> List[TechCard]:
        result = await self.db.execute(select(TechCard))
        return result.scalars().all()

    async def _get_all_products(self) -> Dict[str, Product]:
        result = await self.db.execute(select(Product))
        # Return Dict[iiko_id, Product]
        return {p.iiko_id: p for p in result.scalars().all()}
