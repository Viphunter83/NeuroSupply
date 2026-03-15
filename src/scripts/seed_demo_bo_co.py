
import asyncio
import logging
from sqlalchemy import select, update
from src.db.session import async_session_maker
from src.db.models.product import Product, TechCard
from src.db.models.analytics import ProductMix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESTAURANT_ID = "f9f2e1a9-39ec-4787-8642-5d8879bffc02" # DNL

# Target Dish
DISH_NAME = "Фо Бо"
DISH_ID = "1a7719b7-c003-4e7e-8a0b-3fa3561f8390"
DISH_IIKO_MIX_NAME = "Фо Бо (доставка)"

# Ingredients
INGREDIENTS = [
    {"name": "Говядина тушеная", "id": "bf144430-f8dd-4d45-9c03-7def7e2d377d", "amount": 0.150},
    {"name": "Лапша Фо", "id": "34710f8a-96f8-4744-804f-96596503011d", "amount": 0.200},
    {"name": "Лук зеленый", "id": "2ac3029e-109e-48e5-b264-9a7864dcf57a", "amount": 0.020},
]

async def seed_bo_co():
    async with async_session_maker() as session:
        logger.info(f"Seeding scenario for {RESTAURANT_ID}...")
        
        # 1. Update ProductMix to link the dish
        await session.execute(
            update(ProductMix)
            .where(ProductMix.restaurant_id == RESTAURANT_ID)
            .where(ProductMix.iiko_dish_id == DISH_IIKO_MIX_NAME)
            .values(product_id=DISH_ID)
        )
        logger.info(f"Linked {DISH_IIKO_MIX_NAME} to product ID {DISH_ID}")

        # 2. Clear existing tech cards for this dish to avoid duplicates
        # (Assuming we want a clean demo state)
        # delete_stmt = delete(TechCard).where(TechCard.iiko_dish_id == DISH_ID)
        # await session.execute(delete_stmt)

        # 3. Create TechCards
        for ing in INGREDIENTS:
            tc = TechCard(
                iiko_dish_id=DISH_ID, # Use product ID as iiko_dish_id for consistency in calculation engine
                product_id=ing["id"],
                gross_amount=ing["amount"]
            )
            session.add(tc)
            logger.info(f"Added tech card: {DISH_NAME} -> {ing['name']} ({ing['amount']})")

        await session.commit()
        logger.info("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_bo_co())
