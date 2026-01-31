
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
        
        # Get External Menus
        # Endpoint: /api/1/external_menus
        # Payload: { "organizationIds": ["..."] }
        
        url = f"{client.base_url}/external_menus"
        payload = {"organizationIds": [settings.IIKO_ORG_ID]}
        
        logger.info(f"Fetching external menus for Org: {settings.IIKO_ORG_ID}")
        
        resp = await client.client.post(url, json=payload, headers=client._auth_header())
        resp.raise_for_status()
        menus = resp.json().get("externalMenus", [])
        
        logger.info(f"Found {len(menus)} external menus:")
        for menu in menus:
            logger.info(f"ID: {menu['id']}, Name: {menu['name']}, Description: {menu.get('description', '')}")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
