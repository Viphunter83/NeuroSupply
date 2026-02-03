
import asyncio
import logging
from datetime import datetime, timedelta
from src.services.iiko.client import IikoClient
from src.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    client = IikoClient()
    
    try:
        # 1. Auth
        logger.info("Authenticating...")
        token = await client.auth()
        logger.info(f"Token obtained: {token[:10]}...")
        
        # 2. Get Organizations to find a valid ID
        logger.info("Fetching organizations...")
        orgs = await client.get_organizations()
        if not orgs:
            logger.error("No organizations found!")
            return

        organization_id = orgs[0]['id']
        org_name = orgs[0].get('name')
        logger.info(f"Using Organization: {org_name} ({organization_id})")

        # 3. Test OLAP Sales
        # Fetch last 7 days
        date_to = datetime.now().strftime("%Y-%m-%d")
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        logger.info(f"Fetching OLAP Sales from {date_from} to {date_to}...")
        
        sales_data = await client.get_sales_olap(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to
        )
        
        data = sales_data.get('data', [])
        logger.info(f"Response received. Records count: {len(data)}")
        
        if data:
            logger.info("First 3 records:")
            for item in data[:3]:
                logger.info(item)
        else:
            logger.warning("No sales data returned for this period.")

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
