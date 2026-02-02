import sys
import os
import asyncio
import uuid
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict

sys.path.append(os.getcwd())

from src.core.config import settings
from src.db.session import engine
from src.db.models import Restaurant, Product, ProductMix
from src.services.data_loader.sheets_client import SheetsClient
from src.services.order_service import OrderService
from src.services.calculation.engine_v2 import CalculationEngineV2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_calc():
    logger.info("Starting Daily Calculation...")
    
    sheets = SheetsClient()
    
    # Get Today's Plan
    today_str = datetime.now().strftime("%d.%m.%Y")
    logger.info(f"Fetching Plan for {today_str}...")
    
    sales_plan_rub = sheets.get_plan_for_date(today_str)
    
    if sales_plan_rub <= 0:
        logger.warning(f"No plan found for {today_str} in '2. ПЛАН ПРОДАЖ 📅'. Using fallback 50000.")
        sales_plan_rub = 50000.0
    else:
        logger.info(f"✅ Found Daily Plan: {sales_plan_rub} RUB")

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # 1. Get Restaurant
        # Dynamic ID from Sheets
        org_id = sheets.get_active_restaurant_id()
        if not org_id:
            logger.error("No Active Restaurant ID found.")
            return

        res = await session.execute(select(Restaurant).where(Restaurant.iiko_id == org_id))
        restaurant = res.scalar_one_or_none()
        
        if not restaurant:
            # Fallback
            res = await session.execute(select(Restaurant).limit(1))
            restaurant = res.scalar_one_or_none()
        
        if not restaurant:
            logger.error("No restaurant found.")
            return

        rest_id = restaurant.id
        logger.info(f"Restaurant: {restaurant.name}")

        # 2. Plan is already fetched above

        
        # 3. Calculate Draft Order (Ingredients)
        svc = OrderService(session)
        # This calculates ingredients and saves Order to DB
        order = await svc.generate_draft_order(rest_id, sales_plan_rub)
        logger.info(f"Draft Order Generated: {order.id}")
        
        # 4. Calculate Dish Needs (for Tab 2a)
        # Fetch Mix
        stmt = select(ProductMix).where(ProductMix.restaurant_id == rest_id)
        mixes = (await session.execute(stmt)).scalars().all()
        
        calc_rows = []
        
        # Fetch Products to get names
        dish_ids = [uuid.UUID(pm.iiko_dish_id) for pm in mixes]
        if dish_ids:
            p_stmt = select(Product).where(Product.id.in_(dish_ids))
            products = (await session.execute(p_stmt)).scalars().all()
            p_map = {str(p.id): p for p in products}
        else:
            p_map = {}

        total_qty = 0
        for pm in mixes:
            # Probability is Qty Factor (Qty per 1000 RUB)
            factor = float(pm.probability)
            qty = (sales_plan_rub / 1000.0) * factor
            
            dish_id_str = str(pm.iiko_dish_id)
            dish = p_map.get(dish_id_str)
            name = dish.name_ru if dish else "Unknown"
            
            # Columns: Dish, Plan, Factor, Calc Qty
            calc_rows.append([name, sales_plan_rub, factor, round(qty, 2)])
            total_qty += qty
        
        # 5. Update Sheet Tab 2a
        # '2a. РАСЧЕТ БЛЮД 🍳'
        logger.info(f"Updating '2a. РАСЧЕТ БЛЮД 🍳' with {len(calc_rows)} rows...")
        header = ["Блюдо", "План (Руб)", "К-во на 1000р", "Расчет (шт)"]
        
        # Clear range logic inside sheets client or just update
        # We use update_worksheet which overwrites
        sheets.clear_worksheet("2а. РАСЧЕТ БЛЮД 🍳")
        sheets.update_worksheet("2а. РАСЧЕТ БЛЮД 🍳", [header] + calc_rows)
        
        logger.info("Done!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_calc())
