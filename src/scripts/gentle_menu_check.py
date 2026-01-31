
import asyncio
import logging
import json
import os
from src.services.iiko.client import IikoClient
from src.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting gentle menu check...")
    client = IikoClient()
    
    try:
        # Auth
        await client.auth()
        
        # Single Menu Request
        logger.info(f"Fetching menu for Org: {settings.IIKO_ORG_ID}")
        menu = await client.get_menu(settings.IIKO_ORG_ID)
        
        products = menu.get("products", [])
        groups = menu.get("groups", [])
        revision = menu.get("revision")
        
        logger.info(f"Response - Revision: {revision}")
        logger.info(f"Response - Products count: {len(products)}")
        logger.info(f"Response - Groups count: {len(groups)}")
        
        if products:
             logger.info("Products found! Sample:")
             for p in products[:3]:
                 logger.info(f"- {p.get('name')} ({p.get('price', 'N/A')})")
        else:
            logger.warning("Products list is still empty.")

        # Dump to file for inspection
        os.makedirs("debug_data", exist_ok=True)
        with open("debug_data/gentle_menu.json", "w", encoding="utf-8") as f:
            json.dump(menu, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"Error during gentle check: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
