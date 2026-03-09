import asyncio
import logging
import uuid
from datetime import datetime, timedelta, date
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import async_session_maker as SessionLocal
from src.db.models import SalesFact, Restaurant
from src.services.iiko.client import IikoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_history(days: int = 180):
    """
    Syncs sales history from iiko to SalesFact table.
    Default: Last 180 days (6 months).
    """
    client = IikoClient()
    
    async with SessionLocal() as db:
        try:
            # 1. Get Restaurant
            stmt = select(Restaurant)
            res = await db.execute(stmt)
            restaurants = res.scalars().all()
            
            if not restaurants:
                logger.error("No restaurants found in database. Please run seed_logic.py first.")
                return

            target_restaurant = restaurants[0] # For MVP we take the first one or logic from Settings
            restaurant_id = target_restaurant.id
            iiko_org_id = settings.IIKO_ORG_ID or str(target_restaurant.iiko_id)
            
            logger.info(f"Syncing history for {target_restaurant.name} (Org: {iiko_org_id})")

            # 2. Auth iiko
            await client.auth()

            # 3. Iterate in 7-day chunks (to avoid large responses/timeouts)
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            current_date = start_date
            total_records = 0
            
            while current_date < end_date:
                chunk_end = min(current_date + timedelta(days=7), end_date)
                
                logger.info(f"--- Fetching {current_date} to {chunk_end} ---")
                
                try:
                    # Use the new resto API method
                    # Convert date to datetime if needed
                    date_from = datetime.combine(current_date, datetime.min.time())
                    date_to = datetime.combine(chunk_end, datetime.min.time())
                    
                    report = await client.get_sales_olap_resto(date_from, date_to)
                    data = report.get("data", [])
                    
                    if not data:
                        logger.info("No data for this chunk.")
                    else:
                        # 4. Save to DB
                        # Clean old data for this period to avoid duplicates (Upsert pattern)
                        # delete_stmt = delete(SalesFact).where(
                        #     SalesFact.restaurant_id == restaurant_id,
                        #     SalesFact.date >= datetime.combine(current_date, datetime.min.time()),
                        #     SalesFact.date < datetime.combine(chunk_end, datetime.min.time())
                        # )
                        # await db.execute(delete_stmt)
                        
                        records_batch = []
                        for item in data:
                            # Mapping depends on OLAP response structure
                            # We expect 'DishName', 'OpenDate.Typed', 'DishAmountInt', 'DishDiscountSumInt'
                            # iiko OLAP keys are usually CaseSensitive and depend on query headers.
                            
                            dish_name = item.get("DishName", "Unknown Dish")
                            # iiko_dish_id might not be in OLAP by default unless requested.
                            # We use a deterministic UUID based on dish_name if iiko_id not found.
                            if "DishId" in item:
                                dish_id = item.get("DishId")
                            else:
                                dish_id = str(uuid.uuid5(uuid.NAMESPACE_OID, dish_name))
                            
                            qty = float(item.get("DishAmountInt", 0))
                            rev = float(item.get("DishSumInt", 0)) # Using total sum
                            
                            date_str = item.get("OpenDate.Typed", current_date.strftime("%Y-%m-%d"))
                            try:
                                record_date = datetime.strptime(date_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                            except:
                                record_date = datetime.combine(current_date, datetime.min.time())

                            records_batch.append(SalesFact(
                                id=uuid.uuid4(),
                                restaurant_id=restaurant_id,
                                iiko_dish_id=dish_id,
                                dish_name=dish_name,
                                date=record_date,
                                quantity=qty,
                                revenue_rub=rev
                            ))
                        
                        db.add_all(records_batch)
                        await db.commit()
                        total_records += len(records_batch)
                        logger.info(f"Imported {len(records_batch)} records.")
                        
                except Exception as chunk_err:
                    logger.error(f"Error in chunk {df_str}: {chunk_err}")
                    await db.rollback()

                current_date = chunk_end

            logger.info(f"SUCCESS! Total records imported: {total_records}")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            await db.rollback()
        finally:
            await client.close()

if __name__ == "__main__":
    asyncio.run(sync_history())
