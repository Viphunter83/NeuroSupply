"""
Sync daily sales facts from iiko resto OLAP → sales_facts table.
Runs daily at 02:00 via scheduler.

Fetches yesterday's sales data, maps dish names/IDs, and upserts into sales_facts.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone, date

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.iiko.client import IikoClient
from src.db.session import async_session_maker
from src.db.models.analytics import SalesFact
from src.db.models.restaurant import Restaurant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_sales_facts(days_back: int = 1):
    """
    Fetches sales data from iiko resto OLAP for the last N days
    and syncs to sales_facts table.
    
    Strategy: DELETE existing records for the date range → INSERT fresh.
    This ensures idempotency on re-runs.
    """
    client = IikoClient()
    try:
        date_to = datetime.now(timezone.utc)
        date_from = date_to - timedelta(days=days_back)
        
        date_from_str = date_from.strftime('%Y-%m-%d')
        date_to_str = date_to.strftime('%Y-%m-%d')
        
        logger.info(f"Fetching sales data from {date_from_str} to {date_to_str}...")
        raw_data = await client.get_sales_daily_resto(date_from_str, date_to_str)
        
        if not raw_data:
            logger.warning("No sales data returned from iiko.")
            return
        
        logger.info(f"Received {len(raw_data)} sales rows from iiko.")
        
        async with async_session_maker() as session:
            # 1. Load restaurants for mapping
            rest_stmt = select(Restaurant)
            rest_res = await session.execute(rest_stmt)
            restaurants = rest_res.scalars().all()
            
            # For now, use the first restaurant as default
            # In multi-restaurant setup, the OLAP report should include Department
            default_restaurant = restaurants[0] if restaurants else None
            
            if not default_restaurant:
                logger.error("No restaurants found in DB. Cannot sync sales.")
                return
            
            # 2. Delete existing records for the date range (idempotent)
            delete_from = date_from.date()
            delete_to = date_to.date()
            
            await session.execute(
                delete(SalesFact).where(
                    and_(
                        SalesFact.restaurant_id == default_restaurant.id,
                        SalesFact.date >= delete_from,
                        SalesFact.date <= delete_to
                    )
                )
            )
            
            # 3. Insert fresh data
            inserted = 0
            skipped = 0
            
            for row in raw_data:
                dish_name = row.get('DishName', '').strip()
                dish_id = row.get('DishId', '').strip()
                qty = row.get('DishAmountInt', 0)
                revenue = row.get('DishSumInt', 0)
                date_str = row.get('OpenDate.Typed', '')
                
                if not dish_name or not date_str:
                    skipped += 1
                    continue
                
                # Parse date
                try:
                    fact_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S').date()
                except (ValueError, TypeError):
                    try:
                        fact_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        skipped += 1
                        continue
                
                try:
                    qty_float = float(qty) if qty else 0.0
                    revenue_float = float(revenue) if revenue else 0.0
                except (ValueError, TypeError):
                    skipped += 1
                    continue
                
                fact = SalesFact(
                    restaurant_id=default_restaurant.id,
                    iiko_dish_id=dish_id or dish_name,
                    dish_name=dish_name,
                    date=fact_date,
                    quantity=qty_float,
                    revenue_rub=revenue_float
                )
                session.add(fact)
                inserted += 1
            
            await session.commit()
            logger.info(f"✅ Sales facts synced: {inserted} inserted, {skipped} skipped.")
    
    except Exception as e:
        logger.error(f"❌ Sales facts sync failed: {e}", exc_info=True)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(sync_sales_facts(days_back=1))
