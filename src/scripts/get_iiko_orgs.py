
import asyncio
from src.services.iiko.client import IikoClient
from src.core.config import settings
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        client = IikoClient()
        logger.info(f"Connecting with API Key: {settings.IIKO_API_KEY[:5]}...")
        
        # Authenticate first
        await client.auth()
        
        # Get organizations
        orgs = await client.get_organizations()
        
        logger.info(f"Found {len(orgs)} organizations:")
        for org in orgs:
            logger.info(f"ID: {org['id']}, Name: {org['name']}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
