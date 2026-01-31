import asyncio
import uuid
import pandas as pd
import random
from sqlalchemy import select, delete
from src.db.session import async_session_maker
from src.db.models import Product, Restaurant, TechCard, ProductMix, StockBalance

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
        # Optional: Delete old products? Yes, to avoid duplicates if running multiple times
        # But allow maintaining foreign keys if needed? 
        # For this iteration, let's Wipe Products too to ensure clean state.
        # But we need to handle cascade if Orders exist.
        # Let's hope cascade works or we catch errors.
        # Actually proper way: delete items first.
        # For dev speed: just try to insert, if exists - skip? 
        # No, clean slate is better for "Real Data" pivot.
        
        # We need to preserve the Restaurant though!
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
        await session.flush() # to get IDs
        
        # 2. Generate Tech Cards
        print("Generating Tech Cards...")
        tech_cards = []
        product_ids = [p.id for p in products]
        
        for dish_name, dish_id in DEMO_DISHES.items():
            # Randomly pick 3-5 ingredients
            num_ingredients = random.randint(3, 5)
            ingredients = random.sample(product_ids, num_ingredients)
            
            for ing_id in ingredients:
                tc = TechCard(
                    iiko_dish_id=dish_id,
                    product_id=ing_id,
                    gross_amount=round(random.uniform(0.1, 0.5), 3) # 0.1 to 0.5 kg/unit
                )
                tech_cards.append(tc)
                
        session.add_all(tech_cards)
        
        # 3. Generate Product Mix (Sales Stats)
        print("Generating Product Mix...")
        mixes = []
        for dish_name, dish_id in DEMO_DISHES.items():
            # Probability: 0.2 to 2.0 dishes per 1000 RUB
            prob = round(random.uniform(0.2, 2.0), 2)
            pm = ProductMix(
                restaurant_id=TEST_RESTAURANT_ID,
                iiko_dish_id=str(dish_id), # Storing as string in DB
                probability=prob
            )
            mixes.append(pm)
            
        session.add_all(mixes)
        
        await session.commit()
        print("Data ingestion complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
