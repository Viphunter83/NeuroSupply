import asyncio
import logging
import uuid
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session_maker as SessionLocal
from src.db.models import SalesFact, ProductMix, Restaurant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_mix(days: int = 30):
    """
    Calculates ProductMix based on sales history from last N days.
    Formula: Probability = (Total Dish Qty) / (Total Revenue / 1000)
    """
    async with SessionLocal() as db:
        try:
            # 1. Get Restaurants
            stmt_res = select(Restaurant)
            res_res = await db.execute(stmt_res)
            restaurants = res_res.scalars().all()
            
            for rest in restaurants:
                logger.info(f"Processing ProductMix for {rest.name}...")
                
                # 2. Calculate Total Revenue and Qty per Dish
                # We filter by date if needed
                stmt_sums = select(
                    SalesFact.iiko_dish_id,
                    SalesFact.dish_name,
                    func.sum(SalesFact.quantity).label("total_qty"),
                    func.sum(SalesFact.revenue_rub).label("total_rev")
                ).where(
                    SalesFact.restaurant_id == rest.id
                ).group_by(
                    SalesFact.iiko_dish_id, SalesFact.dish_name
                )
                
                result_sums = await db.execute(stmt_sums)
                sums = result_sums.all()
                
                if not sums:
                    logger.warning(f"No SalesFact data found for restaurant {rest.name}")
                    continue
                
                total_revenue = sum(float(s.total_rev) for s in sums)
                if total_revenue == 0:
                    logger.warning(f"Total revenue is 0 for restaurant {rest.name}")
                    continue
                
                logger.info(f"Total Revenue: {total_revenue:.2f} RUB")
                
                # 3. Clear old Mix for this restaurant
                await db.execute(delete(ProductMix).where(ProductMix.restaurant_id == rest.id))
                
                # 4. Create new Mix records
                mix_records = []
                for dish_id, dish_name, qty, rev in sums:
                    # Probability = Qty per 1000 RUB
                    prob = (float(qty) / (total_revenue / 1000.0))
                    
                    logger.info(f" - Dish: {dish_name} | Qty: {qty} | Prob: {prob:.4f}")
                    
                    mix_records.append(ProductMix(
                        id=uuid.uuid4(),
                        restaurant_id=rest.id,
                        iiko_dish_id=dish_id,
                        probability=prob
                    ))
                
                db.add_all(mix_records)
                await db.commit()
                logger.info(f"SUCCESS: Updated {len(mix_records)} mix records for {rest.name}")

        except Exception as e:
            logger.error(f"Failed to update ProductMix: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(update_mix())
