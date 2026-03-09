import os
import sys
import json
import uuid
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/api/v1"
RESTAURANT_ID = "7cef3937-c383-45f5-aa6f-d4e71db2de06"

def run_tests():
    logger.info("--- STARTING E2E NEUROSUPPLY TESTS ---")
    
    # We don't send Telegram auth header, so backend defaults to Dev user.
    headers = {}
    
    try:
        # 1. Fetch Latest Draft 
        logger.info("[COOK FLOW] Fetching latest draft order...")
        resp = httpx.get(f"{API_URL}/order/latest?restaurant_id={RESTAURANT_ID}", headers=headers)
        
        if resp.status_code != 200:
            logger.error(f"Failed to fetch draft: {resp.text}")
            return
            
        order = resp.json()
        order_id = order['id']
        items = order['items']
        logger.info(f"✅ Found Draft Order: {order_id} with {len(items)} items")
        
        # 2. Modify Stock & Add Extra Item
        logger.info("[COOK FLOW] Simulating stock modification and extra items...")
        if len(items) > 0:
            # Modify first item
            mod_item = items[0]
            old_qty = mod_item.get('quantity', 0)
            mod_item['stock'] = 2.0
            # Simulating deduction (new_qty = original - stock)
            mod_item['quantity'] = max(0, old_qty - 2.0)
            mod_item['comment'] = "Нашел 2 пачки на складе"
            logger.info(f"   Modified Item: {mod_item['product_name']} -> New Qty: {mod_item['quantity']}")
            
        # Add Extra Item
        extra_item = {
            "product_id": str(uuid.uuid4()),
            "product_name": "Тестовый Доп Товар",
            "unit": "шт",
            "quantity": 5.0,
            "quantity_kg": 5.0,
            "predicted_usage": 0,
            "stock": 0,
            "comment": "Срочный дозаказ"
        }
        items.append(extra_item)
        logger.info("   Added Extra Item: Тестовый Доп Товар (5 шт)")
        
        # 3. Save Changes (PUT)
        logger.info("[COOK FLOW] Saving changes to Draft...")
        put_resp = httpx.put(f"{API_URL}/order/{order_id}", json={"items": items}, headers=headers)
        if put_resp.status_code != 200:
            logger.error(f"Failed to PUT items: {put_resp.text}")
            return
        logger.info("✅ Successfully updated draft order items")
        
        # 4. Confirm Order (POST)
        logger.info("[COOK FLOW] Confirming order...")
        conf_resp = httpx.post(f"{API_URL}/order/{order_id}/confirm", headers=headers)
        if conf_resp.status_code != 200:
            logger.error(f"Failed to Confirm: {conf_resp.text}")
            return
        
        final_order = conf_resp.json()
        logger.info(f"✅ Order status after confirm: {final_order['status']}")
        
        # 5. Manager / Admin Export
        logger.info("[ADMIN FLOW] Exporting order to Excel...")
        exp_resp = httpx.get(f"{API_URL}/order/{order_id}/export/excel", headers=headers)
        if exp_resp.status_code == 200:
            logger.info("✅ Successfully generated Excel Export")
            with open(f"/tmp/order_export_{order_id[:8]}.xlsx", "wb") as f:
                f.write(exp_resp.content)
            logger.info(f"   Saved to /tmp/order_export_{order_id[:8]}.xlsx")
        else:
             logger.error(f"Failed to Export: {exp_resp.text}")
             
        logger.info("--- E2E TESTS COMPLETED SUCCESSFULLY ---")

    except Exception as e:
        logger.error(f"Error during E2E: {e}")

if __name__ == "__main__":
    run_tests()
