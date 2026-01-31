
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
    logger.info("Starting Tech Cards fetch...")
    client = IikoClient()
    
    try:
        # Auth
        await client.auth()
        
        # Tech Cards Request
        org_id = settings.IIKO_ORG_ID
        logger.info(f"Fetching tech cards for Org: {org_id}")
        
        # Note: Depending on permissions, this might require specific rights
        tech_cards = await client.get_tech_cards(org_id)
        
        logger.info(f"Response - Tech Cards count: {len(tech_cards)}")
        
        if tech_cards:
             logger.info("Tech Terms found! Sample:")
             for tc in tech_cards[:1]:
                 logger.info(f"Dish ID: {tc.get('id')}")
                 logger.info(f"Ingredients count: {len(tc.get('items', []))}")
        else:
            logger.warning("Tech Cards list is empty. Check permissions or menu items.")

        # Dump to file
        os.makedirs("debug_data", exist_ok=True)
        with open("debug_data/iiko_techcards.json", "w", encoding="utf-8") as f:
            json.dump(tech_cards, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"Error fetching tech cards: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
