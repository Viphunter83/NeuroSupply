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


async def run_calc_for_restaurant(restaurant_id: uuid.UUID, sales_plan_override: float = None):
    """
    Runs calculation for a specific restaurant.
    Uses SalesPlan from DB.
    """
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # 1. Get Restaurant
        restaurant = await session.get(Restaurant, restaurant_id)
        if not restaurant:
            logger.error(f"Restaurant {restaurant_id} not found.")
            return

        logger.info(f"--- [Calculation] {restaurant.name} ---")
        
        # 2. Get Today's Plan
        sales_plan_rub = sales_plan_override
        if not sales_plan_rub:
            from src.db.models import SalesPlan
            from datetime import date
            plan_stmt = select(SalesPlan).where(
                SalesPlan.restaurant_id == restaurant_id,
                SalesPlan.date == date.today()
            )
            plan_res = await session.execute(plan_stmt)
            plan = plan_res.scalar_one_or_none()
            sales_plan_rub = float(plan.amount_rub) if plan else 0.0
            
            if sales_plan_rub <= 0:
                logger.warning(f"⚠️ No sales plan for {date.today()} for {restaurant.name} in DB. Skipping.")
                return

        # 3. Generate Draft Order
        svc = OrderService(session)
        order = await svc.generate_draft_order(restaurant.id, sales_plan_rub)
        logger.info(f"✅ Draft Order Generated: {order.id}")
        
        # Note: We no longer write to Google Sheets. 
        # Results are available via API/Dashboard.

async def run_calc():
    """
    Main entry point for scheduler. Processes all restaurants.
    """
    logger.info("🚀 Starting global order calculation for all restaurants...")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        stmt = select(Restaurant).where(Restaurant.spreadsheet_id != None)
        result = await session.execute(stmt)
        restaurants = result.scalars().all()
        
        for rest in restaurants:
            try:
                await run_calc_for_restaurant(rest.id)
            except Exception as e:
                logger.error(f"Failed calc for {rest.name}: {e}")
    
    logger.info("✅ Global calculation completed.")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Order Calculation")
    parser.add_argument("--restaurant-id", type=str, help="UUID of the restaurant")
    parser.add_argument("--all", action="store_true", help="Run for all restaurants")
    
    args = parser.parse_args()
    
    if args.all:
        await run_calc()
    elif args.restaurant_id:
        try:
            r_id = uuid.UUID(args.restaurant_id)
            await run_calc_for_restaurant(r_id)
        except ValueError:
            logger.error("Invalid UUID format.")
    else:
        parser.print_help()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
