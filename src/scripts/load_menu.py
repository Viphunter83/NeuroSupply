
import asyncio
import logging
import os
from src.db.session import async_session_maker
from src.services.data_loader.menu_parser import MenuParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Menu Load...")
    
    # Target file
    filepath = "debug_data/gentle_menu.json"
    
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return

    parser = MenuParser(filepath)
    
    try:
        dishes = parser.parse()
        logger.info(f"Parsed {len(dishes)} dishes.")
        
        if dishes:
            logger.info("Sample Parsed Dish:")
            logger.info(dishes[0])
            
        # Async DB Session
        async with async_session_maker() as db:
            await parser.save_to_db(db, dishes)
            logger.info("Successfully saved Dishes to DB.")
            
    except Exception as e:
        logger.error(f"Error loading menu: {e}")

if __name__ == "__main__":
    asyncio.run(main())
