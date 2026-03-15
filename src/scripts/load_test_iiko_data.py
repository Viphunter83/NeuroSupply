
import asyncio
import logging
import os
from datetime import datetime, timedelta
from src.services.iiko.client import IikoClient
from src.core.config import settings

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_load_test():
    client = IikoClient()
    try:
        logger.info("--- STARTING IIKO LOAD TEST (30 DAYS HISTORY) ---")
        
        # 1. Authenticate
        logger.info("Authenticating with iiko Chain Server...")
        await client.resto_auth()
        
        # 2. Define Date Range (Last 30 Days)
        date_to = datetime.now()
        date_from = date_to - timedelta(days=30)
        
        logger.info(f"Fetching OLAP sales from {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}...")
        
        # 3. Fetch Data
        start_time = asyncio.get_event_loop().time()
        sales_data = await client.get_sales_olap_resto(date_from, date_to)
        end_time = asyncio.get_event_loop().time()
        
        fetch_duration = end_time - start_time
        logger.info(f"Data fetch completed in {fetch_duration:.2f} seconds.")
        
        # 4. Analyze Data
        rows = sales_data.get('data', [])
        logger.info(f"Total sales records retrieved: {len(rows)}")
        
        if not rows:
            logger.warning("No sales data found for the selected period.")
            return

        logger.info(f"Sample data row: {rows[0]}")

        # Simple Analytics
        dish_stats = {}
        total_revenue = 0
        total_qty = 0
        
        for row in rows:
            # Check if row is list or dict
            if isinstance(row, dict):
                dish_name = row.get("DishName")
                qty = float(row.get("DishAmountInt", 0))
                revenue = float(row.get("DishSumInt", 0))
            else:
                # Fallback for list format
                dish_name = row[1]
                qty = float(row[3])
                revenue = float(row[4])
            
            total_qty += qty
            total_revenue += revenue
            
            if dish_name not in dish_stats:
                dish_stats[dish_name] = {"qty": 0, "rev": 0}
            
            dish_stats[dish_name]["qty"] += qty
            dish_stats[dish_name]["rev"] += revenue
            
        logger.info(f"Total Revenue: {total_revenue:,.2f} RUB")
        logger.info(f"Total Items Sold: {total_qty:,.0f}")
        
        # Top 10 Dishes by Quantity
        top_dishes = sorted(dish_stats.items(), key=lambda x: x[1]["qty"], reverse=True)[:10]
        
        logger.info("--- TOP 10 DISHES (BY QUANTITY) ---")
        for i, (name, stats) in enumerate(top_dishes, 1):
            logger.info(f"{i}. {name}: {stats['qty']:.0f} units | {stats['rev']:,.2f} RUB")

        # 5. Performance Check
        # Here we would normally feed this to the prediction algorithm
        # For now, let's log the memory/complexity
        logger.info(f"Unique dishes found: {len(dish_stats)}")
        logger.info("--- LOAD TEST COMPLETED SUCCESSFULLY ---")

    except Exception as e:
        logger.error(f"Load test FAILED: {e}", exc_info=True)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(run_load_test())
