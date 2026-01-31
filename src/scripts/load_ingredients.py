
import asyncio
import logging
import os
from src.db.session import async_session_maker
from src.services.data_loader.ingredients_parser import IngredientsParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Ingredients Load...")
    
    # Target file
    filepath = "data_samples/NEW Ежедненвый Даниловский.xlsx"
    
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return

    parser = IngredientsParser(filepath)
    
    try:
        products = parser.parse()
        logger.info(f"Parsed {len(products)} products.")
        
        if products:
            logger.info("Sample Parsed Product:")
            logger.info(products[0])
            
        # Async DB Session
        async with async_session_maker() as db:
            await parser.save_to_db(db, products)
            logger.info("Successfully saved to DB.")
            
    except Exception as e:
        logger.error(f"Error loading ingredients: {e}")

if __name__ == "__main__":
    asyncio.run(main())
