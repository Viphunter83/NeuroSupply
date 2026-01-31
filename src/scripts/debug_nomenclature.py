
import asyncio
import logging
from src.services.iiko.client import IikoClient
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_menu():
    client = IikoClient()
    try:
        await client.auth()
        orgs = await client.get_organizations()
        if not orgs:
            logger.error("No organizations found")
            return
        
        org_id = orgs[0]['id']
        logger.info(f"Fetching menu for Org ID: {org_id}")
        
        menu = await client.get_menu(org_id)
        logger.info(f"Menu Keys: {list(menu.keys())}")
        
        if "products" in menu:
            logger.info(f"Product count: {len(menu['products'])}")
            if len(menu['products']) > 0:
                logger.info(f"First product sample: {menu['products'][0]}")
        else:
            logger.warning("'products' key NOT found in response.")
            
        if "groups" in menu:
             logger.info(f"Groups count: {len(menu['groups'])}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(debug_menu())
