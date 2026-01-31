
import asyncio
import logging
import random
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models.product import Product
from src.services.calculation.engine import CalculationEngine

from src.services.calculation.exporter import OrderExporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Calculation Engine Test...")
    
    async with async_session_maker() as session:
        # 1. Generate Mock Sales Plan (Dish ID -> Qty)
        result = await session.execute(select(Product).where(Product.category == "Dish"))
        dishes = result.scalars().all()
        
        if not dishes:
            logger.error("No dishes found!")
            return
            
        sales_plan = {}
        logger.info("--- Sales Plan ---")
        for dish in dishes:
            qty = random.randint(10, 50) # Sell 10-50 units of each
            sales_plan[dish.id] = qty
            logger.info(f"{dish.name_ru}: {qty} orders")
            
        # 2. Run Engine
        engine = CalculationEngine(session)
        order_list = await engine.calculate_requirements(sales_plan)
        
        # 3. Output Result
        logger.info("\n--- DRAFT ORDER (Calculation Result) ---")
        for item in order_list:
            logger.info(f"{item['ingredient_name']:<30} | Need: {item['required_amount']:>6.2f} {item['unit']:<4} | Order: {item['order_qty']:>3} {item['order_unit']:<5} | {item['comment']}")

        # 4. Export to Excel
        exporter = OrderExporter(output_path="debug_data")
        file_path = exporter.export_to_excel(order_list)
        logger.info(f"\nSuccessfully saved Excel to: {file_path}")

if __name__ == "__main__":
    asyncio.run(main())
