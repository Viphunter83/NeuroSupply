
import asyncio
import logging
import random
import uuid
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models.product import Product, TechCard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_mock_tech_cards():
    logger.info("Generating Mock Tech Cards...")
    
    async with async_session_maker() as session:
        # Get all Dishes
        result = await session.execute(select(Product).where(Product.category == "Dish"))
        dishes = result.scalars().all()
        
        # Get all Ingredients
        result = await session.execute(select(Product).where(Product.category == "Ingredient"))
        ingredients = result.scalars().all()
        
        if not dishes or not ingredients:
            logger.error("Need both Dishes and Ingredients to mock Tech Cards.")
            return

        tech_cards = []
        
        for dish in dishes:
            # Assign 3-5 random ingredients to each dish
            num_ingredients = random.randint(3, 5)
            selected_ingredients = random.sample(ingredients, num_ingredients)
            
            logger.info(f"Mocking Recipe for Dish: {dish.name_ru}")
            
            for ing in selected_ingredients:
                # Random amount: 0.01 to 0.5 kg/liter/unit
                amount = round(random.uniform(0.01, 0.5), 3)
                
                tc = TechCard(
                    id=uuid.uuid4(),
                    iiko_dish_id=dish.id, # Using internal ID referencing
                    product_id=ing.id,
                    gross_amount=amount
                )
                tech_cards.append(tc)
                logger.info(f"  - {ing.name_ru}: {amount} {ing.unit}")

        # Save to DB
        session.add_all(tech_cards)
        await session.commit()
        logger.info(f"Generated {len(tech_cards)} mock tech card entries.")

if __name__ == "__main__":
    asyncio.run(generate_mock_tech_cards())
