import asyncio
import uuid
from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models.restaurant import Restaurant
from src.db.models.product import Product
from src.db.models.order import Order, OrderStatus

# The ID used in frontend fallback
TEST_RESTAURANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
DUMMY_IIKO_ID = uuid.uuid4()

async def seed():
    async with async_session_maker() as session:
        print("Starting seed...")
        
        # 1. Ensure Restaurant
        result = await session.execute(select(Restaurant).where(Restaurant.id == TEST_RESTAURANT_ID))
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            restaurant = Restaurant(
                id=TEST_RESTAURANT_ID,
                iiko_id=DUMMY_IIKO_ID,
                name="Test Restaurant (MVP)",
                time_zone="Asia/Jakarta",
                settings={"mock": True}
            )
            session.add(restaurant)
            await session.commit()
            print(f"Created Restaurant: {restaurant.id}")
        else:
            print(f"Restaurant exists: {restaurant.id}")

        # 2. Ensure Products
        products = []
        for i in range(1, 4):
            sku = f"MVP-PROD-{i}"
            res = await session.execute(select(Product).where(Product.iiko_id == sku))
            p = res.scalar_one_or_none()
            
            if not p:
                p = Product(
                    id=uuid.uuid4(),
                    iiko_id=sku,
                    name_ru=f"Тестовый Товар {i}",
                    name_vn=f"Sản phẩm {i}",
                    unit="kg",
                    category="Vegetables",
                    shelf_life_days=7
                )
                session.add(p)
                await session.flush() # get ID
                products.append(p)
                print(f"Created Product: {p.name_ru}")
            else:
                products.append(p)
                print(f"Found Product: {p.name_ru}")
        
        await session.commit()

        # 3. Create Draft Order
        result = await session.execute(
            select(Order).where(
                Order.restaurant_id == TEST_RESTAURANT_ID,
                Order.status == OrderStatus.DRAFT
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            # Prepare items list of dicts
            items_json = []
            total = 0.0
            for idx, p in enumerate(products):
                qty = (idx + 1) * 5.0
                price = 100.0 * (idx + 1)
                
                # Helper for image url (random placeholder)
                img_url = f"https://placehold.co/150?text={p.name_ru.replace(' ', '+')}"

                item_dict = {
                    "product_id": str(p.id),
                    "product_name": p.name_ru,
                    "product_name_vn": p.name_vn,
                    "image_url": img_url,
                    "unit": p.unit,
                    "quantity": qty,
                    "predicted_usage": qty * 0.8,
                    "stock": qty * 0.2
                }
                items_json.append(item_dict)
                total += (qty * price)

            order = Order(
                id=uuid.uuid4(),
                restaurant_id=TEST_RESTAURANT_ID,
                status=OrderStatus.DRAFT,
                items=items_json # JSON field
            )
            session.add(order)
            await session.commit()
            print(f"Created Draft Order {order.id} with {len(items_json)} items")
        else:
             # Update items if empty (optional, for safety)
            if not order.items:
                 items_json = []
                 for idx, p in enumerate(products):
                    qty = (idx + 1) * 5.0
                    item_dict = {
                        "product_id": str(p.id),
                        "product_name": p.name_ru,
                        "product_name_vn": p.name_vn,
                        "image_url": None,
                        "unit": p.unit,
                        "quantity": qty,
                        "predicted_usage": qty,
                        "stock": 0
                    }
                    items_json.append(item_dict)
                 order.items = items_json
                 await session.commit()
                 print(f"Updated existing order {order.id} with items")
            else:
                print(f"Draft Order already exists and has items: {order.id}")
            
        print("Seed completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
