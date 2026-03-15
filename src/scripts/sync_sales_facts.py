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
            
            # Map by name (or iiko_id if you prefer, but OLAP Department is often a string name)
            rest_map = {r.name: r.id for r in restaurants}
            rest_ids = [r.id for r in restaurants]
            
            if not rest_ids:
                logger.error("No restaurants found in DB. Cannot sync sales.")
                return
            
            # 2. Delete existing records for the date range for ALL synced restaurants
            # (In a real production system, you might want to be more selective, 
            # but deleting by global date range for the system is simpler for now)
            delete_from = date_from.date()
            delete_to = date_to.date()
            
            await session.execute(
                delete(SalesFact).where(
                    and_(
                        SalesFact.restaurant_id.in_(rest_ids),
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
                department_name = row.get('Department', '').strip()
                department_id_str = row.get('Department.Id', '').strip()
                dish_id = row.get('DishId', '').strip()
                qty = row.get('DishAmountInt', 0)
                revenue = row.get('DishSumInt', 0)
                date_str = row.get('OpenDate.Typed', '')
                
                if not dish_name or not date_str:
                    skipped += 1
                    continue
                
                # Determine restaurant_id using Department.Id (UUID) first
                target_restaurant_id = None
                if department_id_str:
                    try:
                        dept_uuid = uuid.UUID(department_id_str)
                        # Find restaurant by iiko_id
                        for r in restaurants:
                            if r.iiko_id == dept_uuid:
                                target_restaurant_id = r.id
                                break
                    except ValueError:
                        pass
                
                # Fallback to name-based mapping if ID mapping failed
                if not target_restaurant_id:
                    target_restaurant_id = rest_map.get(department_name)
                
                # Ultimate fallback for single-restaurant setups
                if not target_restaurant_id and len(rest_ids) == 1:
                    target_restaurant_id = rest_ids[0]
                
                if not target_restaurant_id:
                    logger.debug(f"Row skipped: unknown department '{department_name}' (ID: {department_id_str})")
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
                    restaurant_id=target_restaurant_id,
                    iiko_dish_id=dish_id or dish_name,
                    dish_name=dish_name,
                    date=fact_date,
                    quantity=qty_float,
                    revenue_rub=revenue_float
                )
                session.add(fact)
                inserted += 1
            
            await session.commit()
            logger.info(f"✅ Sales facts synced: {inserted} inserted, {skipped} skipped across {len(restaurants)} restaurants.")
    
    except Exception as e:
        logger.error(f"❌ Sales facts sync failed: {e}", exc_info=True)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(sync_sales_facts(days_back=1))
