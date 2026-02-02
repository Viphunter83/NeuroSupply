import asyncio
import uuid
import pandas as pd
import random
from sqlalchemy import select, delete
from src.db.session import async_session_maker
from src.db.models import Product, Restaurant, TechCard, ProductMix, StockBalance, SalesPlan

FILE_PATH = "data_samples/Для_кафе_с_Ежедневными_поставками.xlsx"
TEST_RESTAURANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

# Demo Dishes to generate recipes for
DEMO_DISHES = {
    "Pho Bo (Суп с говядиной)": uuid.uuid4(),
    "Pho Ga (Суп с курицей)": uuid.uuid4(),
    "Nem Ran (Нэмы жареные)": uuid.uuid4(),
    "Com Rang (Рис жареный)": uuid.uuid4(),
    "Bun Cha (Бун Ча)": uuid.uuid4()
}

async def seed_data():
    print("Starting data ingestion...")
    
    # 1. Read Excel
    df = pd.read_excel(FILE_PATH, header=None)
    # Data starts roughly at row 2 (index 2)
    # Columns: 0=Idx, 1=NameRU, 2=NameVN, 3=Unit
    
    products = []
    
    print(f"Parsing {FILE_PATH}...")
    for index, row in df.iterrows():
        if index < 2: continue # Skip headers
        
        name_ru = str(row[1]).strip()
        if pd.isna(row[1]) or name_ru == "nan" or name_ru == "":
            continue
            
        name_vn = str(row[2]).strip() if not pd.isna(row[2]) else ""
        unit = str(row[3]).strip() if not pd.isna(row[3]) else "шт"
        
        # Determine category (naive)
        category = "General"
        if "мясо" in name_ru.lower() or "говя" in name_ru.lower(): category = "Meat"
        elif "овощ" in name_ru.lower() or "зелень" in name_ru.lower(): category = "Vegetables"
        elif "соус" in name_ru.lower(): category = "Sauces"
        
        p = Product(
            id=uuid.uuid4(),
            iiko_id=str(uuid.uuid4()), # Fake iiko ID for ingredient
            name_ru=name_ru,
            name_vn=name_vn,
            unit=unit,
            category=category,
            shelf_life_days=3 # Default
        )
        products.append(p)
    
    print(f"Found {len(products)} products.")
    
    async with async_session_maker() as session:
        # Clear old data
        print("Clearing old data...")
        await session.execute(delete(TechCard))
        await session.execute(delete(ProductMix))
        await session.execute(delete(StockBalance))
        await session.execute(delete(SalesPlan))
        # Note: Wiping products might be risky if we have active orders, but for Dev it's ok.
        
        # Check/Create Restaurant
        res = await session.execute(select(Restaurant).where(Restaurant.id == TEST_RESTAURANT_ID))
        restaurant = res.scalar_one_or_none()
        if not restaurant:
             print("Creating Restaurant...")
             restaurant = Restaurant(
                 id=TEST_RESTAURANT_ID,
                 iiko_id=uuid.uuid4(),
                 name="Test Restaurant (Real Data)",
                 time_zone="Asia/Jakarta",
                 settings={}
             )
             session.add(restaurant)
        
        # Add Products
        session.add_all(products)
        await session.flush()
        
        # 2. Generate Tech Cards (Deterministic)
        print("Generating Tech Cards...")
        tech_cards = []
        product_ids = [p.id for p in products]
        
        if product_ids:
            for dish_name, dish_id in DEMO_DISHES.items():
                # Use deterministic seed based on dish_id integer representation
                random.seed(dish_id.int)
                
                num_ingredients = random.randint(3, 5)
                # Ensure we don't sample more than available
                cnt = min(num_ingredients, len(product_ids))
                ingredients = random.sample(product_ids, cnt)
                
                for ing_id in ingredients:
                    tc = TechCard(
                        iiko_dish_id=dish_id,
                        product_id=ing_id,
                        gross_amount=round(random.uniform(0.1, 0.5), 3)
                    )
                    tech_cards.append(tc)
        
        session.add_all(tech_cards)
        
        # 3. Generate Product Mix
        print("Generating Product Mix...")
        mixes = []
        for dish_name, dish_id in DEMO_DISHES.items():
            random.seed(dish_id.int) # Same seed logic
            prob = round(random.uniform(0.2, 2.0), 2)
            pm = ProductMix(
                restaurant_id=TEST_RESTAURANT_ID,
                iiko_dish_id=str(dish_id),
                probability=prob
            )
            mixes.append(pm)
            
        session.add_all(mixes)
        
        # 4. Parse Sales Plan (New)
        try:
            from src.services.data_loader.sales_plan_parser import SalesPlanParser
            from datetime import date
            
            # Using google_export.xlsx (Actual downloaded structure)
            PLAN_FILE = "data_samples/google_export.xlsx"
            parser = SalesPlanParser(PLAN_FILE)
            
            # Parse for current/next month (Mocking: Jan 2026 as per filename?)
            # The file has "Январь 2026". We need to match that. 
            # If today is NOT Jan 2026, the parser will return empty.
            # Let's Force Jan 2026 for testing if needed, or check today.
            # Using code "ANG" because it's in the file.
            today = date.today()
            # FORCE Jan 2026 for this test because the file is static
            year, month = 2026, 1 
            plans = parser.parse(TEST_RESTAURANT_ID, year, month, restaurant_code="ANG")
            if plans:
                print(f"Loaded {len(plans)} sales plan entries.")
                # Dedupe or bulk insert?
                for p_data in plans:
                    sp = SalesPlan(**p_data)
                    session.add(sp)
            else:
                print("No sales plans found in parsed file.")

        except Exception as e:
            print(f"Skipping Sales Plan loading: {e}")

        await session.commit()
        print("Data ingestion complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
