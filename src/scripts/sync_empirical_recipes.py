import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, delete

from src.core.config import settings
from src.services.iiko.client import IikoClient
from src.db.session import async_session_maker
from src.db.models.product import EmpiricalRecipe, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_transaction_data(client: IikoClient, days_back: int = 30):
    url = f"{client.resto_url}/v2/reports/olap"
    token = await client.resto_auth()
    
    all_transactions = []
    
    date_to = datetime.now()
    date_from = date_to - timedelta(days=days_back)
    
    current_from = date_from
    chunk_days = 7
    client.client.timeout = httpx.Timeout(120.0) # Increase timeout just in case
    
    while current_from < date_to:
        current_to = min(current_from + timedelta(days=chunk_days), date_to)
        logger.info(f"Fetching transactions from {current_from.date()} to {current_to.date()}")
        
        json_payload = {
            "reportType": "TRANSACTIONS", 
            "groupByRowFields": [
                "Document", 
                "Product.Name",
                "Contr-Product.Name",
            ],
            "aggregateFields": ["Amount.Out"],
            "filters": {
                "DateTime.DateTyped": {
                    "filterType": "DateRange",
                    "from": current_from.strftime('%Y-%m-%d'),
                    "to": current_to.strftime('%Y-%m-%d')
                }
            }
        }
        
        resp = await client.client.post(url, params={"key": token}, json=json_payload)
        if resp.status_code == 200:
             all_transactions.extend(resp.json().get('data', []))
        else:
             logger.error(f"Failed to fetch TRANSACTIONS chunk: {resp.text}")
             
        current_from = current_to
        
    return all_transactions

async def fetch_sales_data(client: IikoClient, days_back: int = 30):
    url = f"{client.resto_url}/v2/reports/olap"
    token = await client.resto_auth()
    
    all_sales = []
    
    date_to = datetime.now()
    date_from = date_to - timedelta(days=days_back)
    
    current_from = date_from
    chunk_days = 7
    
    while current_from < date_to:
        current_to = min(current_from + timedelta(days=chunk_days), date_to)
        logger.info(f"Fetching sales from {current_from.date()} to {current_to.date()}")
        
        json_payload = {
            "reportType": "SALES",
            "groupByRowFields": ["DishName"],
            "aggregateFields": ["DishAmountInt"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "from": current_from.strftime('%Y-%m-%d'),
                    "to": current_to.strftime('%Y-%m-%d')
                }
            }
        }
        
        resp = await client.client.post(url, params={"key": token}, json=json_payload)
        if resp.status_code == 200:
             all_sales.extend(resp.json().get('data', []))
        else:
             logger.error(f"Failed to fetch SALES chunk: {resp.text}")
             
        current_from = current_to
        
    return all_sales

async def sync_empirical_recipes():
    client = IikoClient()
    try:
        logger.info("Fetching transaction data...")
        transactions = await fetch_transaction_data(client, days_back=30)
        
        logger.info("Fetching sales data for the same period...")
        sales = await fetch_sales_data(client, days_back=30)
        
        logger.info("Fetching iiko menu to map dish names to IDs...")
        menu_data = await client.get_menu(settings.IIKO_ORG_ID)
        menu_items = menu_data.get('products', [])
        name_to_dish_id = {}
        for p in menu_items:
            if p.get('name') and p.get('id'):
                name_to_dish_id[p['name'].strip()] = p['id']

        # 1. Map Sales

        sales_map = {}
        for s in sales:
            name = s.get('DishName')
            qty = s.get('DishAmountInt', 0)
            if name and qty:
                sales_map[name] = sales_map.get(name, 0) + qty
                
        # 2. Map Ingredient Write-Offs
        # dish_name -> {ingredient_name: total_amount_out}
        writeoffs_map = defaultdict(lambda: defaultdict(float))
        
        for tx in transactions:
            dish = tx.get('Contr-Product.Name')
            ingredient = tx.get('Product.Name')
            amount_out = tx.get('Amount.Out', 0)
            
            # Usually, when a dish is written off, Amount.Out > 0 for the ingredients
            if dish and ingredient and dish != ingredient and amount_out > 0:
                writeoffs_map[dish][ingredient] += amount_out
                
        # 3. Calculate Yield Rates
        recipes_to_save = []
        for dish, ingredients in writeoffs_map.items():
            sold_qty = sales_map.get(dish)
            if not sold_qty or sold_qty <= 0:
                continue # Cannot calculate rate if sales are 0 or not found
                
            for ingr_name, total_out in ingredients.items():
                if total_out <= 0: continue
                # Yield rate = total kg written off / total portions sold
                yield_rate = total_out / sold_qty
                
                # Fetch dish_id
                dish_uuid_str = name_to_dish_id.get(dish.strip())
                dish_uuid = None
                if dish_uuid_str:
                    import uuid
                    try:
                        dish_uuid = uuid.UUID(dish_uuid_str)
                    except:
                        pass

                # Filter out absurd rates (e.g. > 1000kg per portion or < 0.0001)
                # Just basic sanity to avoid garbage mappings
                if 0.0001 < yield_rate < 100.0:
                    recipes_to_save.append({
                        "dish_name": dish,
                        "dish_id": dish_uuid,
                        "ingredient_name": ingr_name,
                        "yield_rate": yield_rate
                    })
                    
        logger.info(f"Calculated {len(recipes_to_save)} empirical recipe mappings.")
        
        if not recipes_to_save:
            logger.warning("No recipes calculated. Check OLAP mappings.")
            return

        # 4. Save to Database
        async with async_session_maker() as session:
            # Optionally clear old or just update
            # We will clear table and insert fresh to keep it simple, or upsert.
            await session.execute(delete(EmpiricalRecipe))
            
            # Map ingredients to products where possible
            stmt = select(Product)
            res = await session.execute(stmt)
            products = res.scalars().all()
            prod_map = {p.name_ru: p.id for p in products}
            
            new_objects = []
            for r in recipes_to_save:
                pid = None
                ingr_lower = r['ingredient_name'].lower().strip()
                
                # 1. Exact or near-exact match first
                pid = prod_map.get(r['ingredient_name'])
                
                # 2. Substring match if exact fails
                if not pid:
                    for p in products:
                        if p.name_ru and p.name_ru.lower().strip() in ingr_lower:
                            pid = p.id
                            break
                            
                new_db_model = EmpiricalRecipe(
                    dish_name=r['dish_name'],
                    dish_id=r['dish_id'],
                    ingredient_name=r['ingredient_name'],
                    product_id=pid,
                    yield_rate=r['yield_rate']
                )
                new_objects.append(new_db_model)
                
            session.add_all(new_objects)
            await session.commit()
            logger.info("Successfully saved empirical recipes to database!")

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(sync_empirical_recipes())
