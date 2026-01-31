import asyncio
import uuid
import httpx

ORDER_ID = "7aeb53b3-49e1-44b3-8252-8a7b2d33ebf6" # From previous run
BASE_URL = "http://localhost:8000/api/v1/order"

async def test_update():
    # 1. Get Order
    async with httpx.AsyncClient() as client:
        # We need restaurant_id to fetch latest if we don't use ID directly, 
        # but let's assume we use the ID we know.
        # Wait, the frontend code uses `PUT /api/v1/order/{id}`
        
        # Let's construct a payload that matches what frontend sends
        payload = {
            "items": [
                {
                    "product_id": "9350c885-9ba9-4fcf-9119-9dd250264ffa",
                    "product_name": "Кока кола зеро",
                    "product_name_vn": "Coca cola zero",
                    "image_url": "https://placehold.co/150?text=Test",
                    "unit": "Thùng - 12 cái",
                    "quantity": 60.0, # Changed from 56.08
                    "predicted_usage": 56.08,
                    "stock": 0.0
                }
            ]
        }
        
        print(f"Sending PUT to {BASE_URL}/{ORDER_ID}")
        resp = await client.put(f"{BASE_URL}/{ORDER_ID}", json=payload)
        
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_update())
