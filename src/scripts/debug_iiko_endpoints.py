
import asyncio
import sys
import os
from pathlib import Path
from datetime import date, timedelta
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.config import settings
from src.services.iiko.client import IikoClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("--- Debugging Iiko Endpoints ---")
    iiko = IikoClient()
    
    # 1. Auth
    print("\n1. Testing Auth...")
    try:
        token = await iiko.auth()
        print(f"Auth Success. Token: {token[:10]}...")
    except Exception as e:
        print(f"Auth Failed: {e}")
        return

    # 1b. Organizations
    print("\n1b. Getting Organizations...")
    try:
        orgs = await iiko.get_organizations()
        print(f"Organizations found: {len(orgs)}")
        for o in orgs:
            print(f"- {o['name']} (ID: {o['id']})")
    except Exception as e:
        print(f"Orgs Failed: {e}")

    org_id = settings.IIKO_ORG_ID
    if not org_id:
        print("Set IIKO_ORG_ID!")
        return
        
    # 2. Menu
    print(f"\n2. Testing Get Menu for {org_id}...")
    try:
        menu = await iiko.get_menu(org_id)
        print(f"Menu Success. Items: {len(menu.get('products', []))}")
    except Exception as e:
        print(f"Menu Failed: {e}")

    # 3. OLAP
    print(f"\n3. Testing Get Sales OLAP for {org_id}...")
    today = date.today()
    d_from = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    d_to = today.strftime("%Y-%m-%d")
    
    # Minimal payload
    # Note: client.py has hardcoded payload in get_sales_olap, so we use that.
    try:
        sales = await iiko.get_sales_olap(org_id, d_from, d_to)
        print(f"OLAP Success. Data: {sales}")
    except Exception as e:
        print(f"OLAP Failed: {e}")

    await iiko.close()

if __name__ == "__main__":
    asyncio.run(main())
