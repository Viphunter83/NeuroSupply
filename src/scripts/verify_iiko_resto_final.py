
import asyncio
import logging
from datetime import datetime, timedelta
from src.services.iiko.client import IikoClient
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_resto():
    client = IikoClient()
    try:
        print("--- VERIFYING RESTO API ---")
        
        # 1. Auth
        token = await client.resto_auth()
        print(f"✅ Auth Success. Token: {token}")

        # 2. OLAP Sales
        print("\n[OLAP TEST] Fetching sales for March 3rd, 2026...")
        date_from = datetime(2026, 3, 3)
        date_to = datetime(2026, 3, 3)
        sales_xml = await client.get_sales_olap_resto(date_from, date_to)
        
        print(f"✅ OLAP Success. Response length: {len(sales_xml)}")
        # Print a snippet of the XML to verify content
        if "<data>" in sales_xml:
            snippet = sales_xml[sales_xml.find("<data>"):sales_xml.find("</data>")+7]
            print(f"Data Snippet: {snippet[:500]}...")
        else:
            print("Warning: <data> tag not found in response, but request was successful.")
            print(f"Response start: {sales_xml[:200]}")

        # 3. Tech Cards
        print("\n[TECH CARDS TEST] Fetching ready-for-cooking products...")
        tc_xml = await client.get_tech_cards_resto()
        print(f"✅ Tech Cards Success. Response length: {len(tc_xml)}")
        print(f"Snippet: {tc_xml[:300]}...")

    except Exception as e:
        logger.error(f"Verification FAILED: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(verify_resto())
