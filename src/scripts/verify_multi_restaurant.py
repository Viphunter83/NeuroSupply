import asyncio
import uuid
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.db.session import async_session_maker
from src.db.models import Restaurant, ProductMix, StockBalance, Product, TechCard
from src.services.calculation.engine_v2 import CalculationEngineV2
from sqlalchemy import select, delete

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🧪 Starting Multi-Restaurant Verification...")
    
    async with async_session_maker() as db:
        # 1. Cleanup Test Data
        logger.info("Cleaning up old test data...")
        # Resolve IDs first if needed, or delete by join? SQLAlchemy delete with join is tricky.
        # Simpler: Select IDs by name, then delete.
        
        stmt = select(Restaurant.id).where(Restaurant.name.in_(["Test Rest A", "Test Rest B"]))
        res = await db.execute(stmt)
        existing_ids = res.scalars().all()
        
        if existing_ids:
            await db.execute(delete(ProductMix).where(ProductMix.restaurant_id.in_(existing_ids)))
            await db.execute(delete(Restaurant).where(Restaurant.id.in_(existing_ids)))
            await db.commit()
        
        # 2. Create Restaurants
        r1_id = uuid.uuid4()
        r2_id = uuid.uuid4()
        
        r1 = Restaurant(
            id=r1_id,
            name="Test Rest A",
            iiko_id=uuid.uuid4(),
            spreadsheet_id="test_sheet_id_A"
        )
        r2 = Restaurant(
            id=r2_id,
            name="Test Rest B",
            iiko_id=uuid.uuid4(),
            spreadsheet_id="test_sheet_id_B"
        )
        db.add_all([r1, r2])
        await db.flush() # Get IDs
        
        logger.info(f"Created Restaurants: {r1.id}, {r2.id}")
        
        # 3. Create Shared Product (Ingredients)
        p_ing_id = uuid.uuid4()
        p_ing = Product(
            id=p_ing_id,
            iiko_id=str(uuid.uuid4()),
            name_ru="Tomatoes",
            unit="kg",
            category="ingredient"
        )
        # Check if product exists or upsert
        # Simplify: just add if strictly new or ignore conflict? 
        # For test script, likely safe to add if IDs are random.
        # But let's check if we can reuse an existing one or just make a new one.
        db.add(p_ing)
        
        # 4. Create Tech Cards (Dishes)
        dish_a_id = uuid.uuid4()
        dish_b_id = uuid.uuid4()
        
        # Dish A (Rest A) - Uses Tomatoes
        # Tech Cards are usually global? Or Restaurant specific?
        # TechCard model has 'iiko_dish_id'. ProductMix links Dish to Rest.
        # So TC is global definition of a dish.
        
        tc_a = TechCard(
            id=uuid.uuid4(),
            iiko_dish_id=dish_a_id,
            product_id=p_ing_id,
            gross_amount=1.0 # 1kg per dish
        )
        tc_b = TechCard(
            id=uuid.uuid4(),
            iiko_dish_id=dish_b_id,
            product_id=p_ing_id,
            gross_amount=2.0 # 2kg per dish
        )
        db.add_all([tc_a, tc_b])
        
        # 5. Create Product Mix (Specific to Restaurant)
        pm_a = ProductMix(
            restaurant_id=r1.id,
            iiko_dish_id=str(dish_a_id),
            probability=0.1 # 10%
        )
        pm_b = ProductMix(
            restaurant_id=r2.id,
            iiko_dish_id=str(dish_b_id),
            probability=0.2 # 20%
        )
        db.add_all([pm_a, pm_b])
        
        await db.commit()
        
        # 6. Run Calculation
        engine = CalculationEngineV2(db)
        
        # Plan 10,000 RUB
        # Rest A: 10,000 * 0.1 / 1000 = 1 dish -> 1 * 1.0 = 1.0 kg Tomatoes
        # Rest B: 10,000 * 0.2 / 1000 = 2 dishes -> 2 * 2.0 = 4.0 kg Tomatoes
        
        logger.info("Running Calculation for Rest A...")
        res_a = await engine.calculate_needs(r1.id, 10000.0)
        
        logger.info("Running Calculation for Rest B...")
        res_b = await engine.calculate_needs(r2.id, 10000.0)
        
        # 7. Verification
        qty_a = 0
        qty_b = 0
        
        for item in res_a:
            if item['product_id'] == str(p_ing_id):
                qty_a = item['predicted_usage']
                
        for item in res_b:
            if item['product_id'] == str(p_ing_id):
                qty_b = item['predicted_usage']
                
        logger.info(f"Result A (Expected ~1.0): {qty_a}")
        logger.info(f"Result B (Expected ~4.0): {qty_b}")
        
        if qty_a > 0 and qty_b > 0:
            ratio = qty_b / qty_a
            logger.info(f"Ratio B/A: {ratio} (Expected: 4.0)")
            if abs(ratio - 4.0) < 0.1:
                 logger.info("✅ SUCCESS: Calculations are isolated and ratio is correct!")
            else:
                 logger.error("❌ FAILURE: Ratio mismatch.")
        else:
             logger.error("❌ FAILURE: Zero quantity returned.")

        # Cleanup
        # Delete children first
        await db.execute(delete(ProductMix).where(ProductMix.restaurant_id.in_([r1_id, r2_id])))
        await db.execute(delete(Restaurant).where(Restaurant.id.in_([r1_id, r2_id])))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())
