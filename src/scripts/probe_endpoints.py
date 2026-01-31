
import asyncio
import logging
import httpx
from src.services.iiko.client import IikoClient
from src.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Endpoint Probe...")
    client = IikoClient()
    
    candidates = [
        "/ingredients", 
        "/products", 
        "/recipes", 
        "/techcards",
        "/nomenclature/ingredients" 
    ]
    
    try:
        await client.auth()
        
        for endpoint in candidates:
            url = f"{client.base_url}{endpoint}"
            logger.info(f"Probing {url}...")
            try:
                # Try with standard payload
                payload = {"organizationId": settings.IIKO_ORG_ID}
                resp = await client.client.post(url, json=payload, headers=client._auth_header())
                
                logger.info(f"[{endpoint}] Status: {resp.status_code}")
                if resp.status_code == 200:
                    logger.info(f"SUCCESS! Found valid endpoint: {endpoint}")
                    logger.info(f"Response start: {resp.text[:200]}")
                elif resp.status_code == 401:
                    logger.warning(f"[{endpoint}] 401 Unauthorized (Permission or invalid route)")
                else:
                    logger.warning(f"[{endpoint}] Failed with {resp.status_code}")
                    
            except Exception as e:
                logger.error(f"Error probing {endpoint}: {e}")
                
    except Exception as e:
        logger.error(f"Auth failed: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
