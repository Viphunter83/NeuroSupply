"""
Sync stock balances from iiko resto API → stock_balances table.
Runs daily at 05:00 via scheduler.

Now that the 'products' table is synced with iiko resto nomenclature,
we can map directly by iiko_id (resto UUID).
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.iiko.client import IikoClient
from src.db.session import async_session_maker
from src.db.models.product import StockBalance, Product
from src.db.models.restaurant import Restaurant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_stock_balances():
    """
    Fetches current stock balances from iiko resto API and saves to DB.
    Strategy: DELETE all existing → INSERT fresh (snapshot approach).
    """
    client = IikoClient()
    try:
        # 1. Fetch data from iiko
        logger.info("Fetching stock balances from iiko resto API...")
        raw_data = await client.get_stock_balances_resto()
        
        if not raw_data:
            logger.warning("No stock balance data returned from iiko.")
            return
        
        logger.info(f"Received {len(raw_data)} stock balance rows from iiko.")
        
        async with async_session_maker() as session:
            # 2. Load all products for mapping
            stmt = select(Product)
            res = await session.execute(stmt)
            products = res.scalars().all()
            prod_by_iiko_id: dict[str, Product] = {}
            for p in products:
                if p.iiko_id:
                    prod_by_iiko_id[str(p.iiko_id).lower()] = p
            
            # 3. Load all restaurants
            rest_stmt = select(Restaurant)
            rest_res = await session.execute(rest_stmt)
            restaurants = rest_res.scalars().all()
            rest_by_iiko_id: dict[str, Restaurant] = {}
            for r in restaurants:
                if r.iiko_id:
                    rest_by_iiko_id[str(r.iiko_id).lower()] = r
            default_restaurant = restaurants[0] if restaurants else None
            
            # 4. Clear existing balances
            await session.execute(delete(StockBalance))
            
            # 5. Map and aggregate
            aggregated: dict[tuple, float] = {}
            matched = 0
            skipped = 0
            
            for row in raw_data:
                product_uuid = str(row.get('product', '')).lower().strip()
                store_uuid = str(row.get('store', '')).lower().strip()
                amount = row.get('amount', 0)
                
                try:
                    amount_float = float(amount)
                except (ValueError, TypeError):
                    skipped += 1
                    continue
                    
                if amount_float <= 0:
                    skipped += 1
                    continue
                
                # Direct map by UUID (since products table is now synced from resto)
                product = prod_by_iiko_id.get(product_uuid)
                if not product:
                    skipped += 1
                    continue
                
                # Resolve restaurant
                restaurant = rest_by_iiko_id.get(store_uuid)
                if not restaurant:
                    # In single-restaurant setups, we might fallback, but for production 
                    # it is safer to skip if mapping is missing
                    skipped += 1
                    continue
                
                key = (restaurant.id, product.id)
                aggregated[key] = aggregated.get(key, 0.0) + amount_float
                matched += 1
            
            # 6. Insert aggregated balances
            now = datetime.now(timezone.utc)
            inserted = 0
            for (rest_id, prod_id), total_amount in aggregated.items():
                balance = StockBalance(
                    restaurant_id=rest_id,
                    product_id=prod_id,
                    amount=total_amount,
                    snapshot_at=now
                )
                session.add(balance)
                inserted += 1
            
            await session.commit()
            logger.info(
                f"✅ Stock balances synced: {inserted} products inserted, "
                f"{matched} rows matched, {skipped} skipped "
                f"(from {len(raw_data)} iiko rows)."
            )
    
    except Exception as e:
        logger.error(f"❌ Stock balance sync failed: {e}", exc_info=True)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(sync_stock_balances())
