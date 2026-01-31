
import asyncio
import json
import os
from datetime import datetime, timedelta
from src.services.iiko.client import IikoClient
from src.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def dump_data(data, filename):
    os.makedirs("debug_data", exist_ok=True)
    filepath = f"debug_data/{filename}"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved data to {filepath}")

async def main():
    if not settings.IIKO_ORG_ID:
        logger.error("IIKO_ORG_ID is missing in settings!")
        return

    logger.info(f"Starting discovery for Org ID: {settings.IIKO_ORG_ID}")
    client = IikoClient()
    
    try:
        # Auth
        await client.auth()
        
        # 1. Get Menu (Nomenclature)
        logger.info("Fetching Menu...")
        menu = await client.get_menu(settings.IIKO_ORG_ID)
        await dump_data(menu, "iiko_menu.json")
        
        # 2. Get Terminal Groups (Crucial for orders)
        logger.info("Fetching Terminal Groups...")
        try:
            terminal_groups = await client.get_terminal_groups([settings.IIKO_ORG_ID])
            await dump_data(terminal_groups, "iiko_terminal_groups.json")
            
            # 3. Get Stop Lists (using Organization ID)
            logger.info("Fetching Stop Lists...")
            stop_lists = await client.get_stop_lists([settings.IIKO_ORG_ID])
            await dump_data(stop_lists, "iiko_stop_lists.json")
            
        except Exception as e:
            logger.error(f"Failed to fetch terminals/stop-lists: {e}")

        # 4. Try Sales again (Optional, just logging warning if fails)
        logger.info("Attempting Sales (OLAP) check (expecting failure)...")
        date_to = datetime.now().strftime("%Y-%m-%d")
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        try:
             sales = await client.get_sales_olap(settings.IIKO_ORG_ID, date_from, date_to)
             await dump_data(sales, "iiko_sales_7days.json")
        except Exception:
             logger.warning("OLAP Access denied (expected for 'Orders' integration). Skipping.")
            
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
