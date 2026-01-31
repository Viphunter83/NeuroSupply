
import asyncio
import logging
from src.services.iiko.client import IikoClient
from src.core.config import settings
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if not settings.IIKO_ORG_ID:
        logger.error("No Org ID")
        return

    logger.info("Starting polling for menu updates...")
    client = IikoClient()
    
    try:
        await client.auth()
        
        for i in range(20): # Try 20 times (approx 20 mins)
            logger.info(f"Attempt {i+1}/20...")
            try:
                menu = await client.get_menu(settings.IIKO_ORG_ID)
                products = menu.get("products", [])
                groups = menu.get("groups", [])
                revision = menu.get("revision")
                
                logger.info(f"Revision: {revision}, Products: {len(products)}, Groups: {len(groups)}")
                
                if len(products) > 0:
                    logger.info("SUCCESS! Products found!")
                    # Dump to file
                    import json
                    with open("debug_data/iiko_menu_success.json", "w") as f:
                        json.dump(menu, f, ensure_ascii=False, indent=2)
                    return
                
            except Exception as e:
                logger.error(f"Error fetching menu: {e}")
                
            # Wait 60 seconds
            if i < 19:
                logger.info("Waiting 60 seconds...")
                await asyncio.sleep(60)
                
        logger.warning("Timed out waiting for products.")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
