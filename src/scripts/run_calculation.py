import asyncio
import uuid
import sys
from src.db.session import async_session_maker
from src.services.order_service import OrderService

TEST_RESTAURANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
SALES_PLAN_RUB = 150000.0 # Example plan

async def main():
    print(f"Generating Draft Order for Restaurant {TEST_RESTAURANT_ID}...")
    print(f"Sales Plan: {SALES_PLAN_RUB} RUB")
    
    async with async_session_maker() as session:
        service = OrderService(session)
        try:
            order = await service.generate_draft_order(TEST_RESTAURANT_ID, SALES_PLAN_RUB)
            print(f"Success! Order ID: {order.id}")
            print(f"Items count: {len(order.items)}")
            for item in order.items[:3]:
                print(f" - {item['product_name']}: {item['quantity']} {item['unit']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
