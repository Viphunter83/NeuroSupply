
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from src.services.iiko.client import IikoClient
from src.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Sales History (OLAP) fetch...")
    client = IikoClient()
    
    try:
        await client.auth()
        
        # Date Range: Last 30 days
        date_to = datetime.now().strftime("%Y-%m-%d")
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        org_id = settings.IIKO_ORG_ID
        logger.info(f"Fetching OLAP for Org: {org_id} | {date_from} to {date_to}")
        
        # OLAP Request
        report = await client.get_sales_olap(org_id, date_from, date_to)
        
        data = report.get("data", [])
        logger.info(f"Response - Records count: {len(data)}")
        
        if data:
             logger.info("Sample Record:")
             logger.info(json.dumps(data[0], ensure_ascii=False, indent=2))
        else:
            logger.warning("OLAP report returned empty data.")

        # Dump to file
        os.makedirs("debug_data", exist_ok=True)
        filename = f"debug_data/iiko_sales_olap_{date_from}_{date_to}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved to {filename}")
            
    except Exception as e:
        logger.error(f"Error fetching sales history: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
