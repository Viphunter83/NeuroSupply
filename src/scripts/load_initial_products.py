import asyncio
import sys
import os
import pandas as pd
from sqlalchemy import select

# Add project root to python path
sys.path.append(os.getcwd())

from src.db.session import async_session_factory
from src.db.models import Product

async def main():
    file_path = "data_samples/Для_кафе_с_Ежедневными_поставками.xlsx"
    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path)
    
    # Iterate rows
    async with async_session_factory() as session:
        count = 0
        for index, row in df.iterrows():
            name_ru = row.get('Дата________________________')
            if pd.isna(name_ru) or str(name_ru).strip().lower().startswith('дата'):
                continue
            
            name_vn = row.get('ЕЖЕДНЕВНЫЙ ЗАКАЗ')
            unit_ru = row.get(' v19.08 ')
            
            # Basic cleaning
            name_ru = str(name_ru).strip()
            name_vn = str(name_vn).strip() if not pd.isna(name_vn) else None
            unit = str(unit_ru).strip() if not pd.isna(unit_ru) else "шт"
            
            # Generate a pseudo iiko_id if missing. Use row index.
            # In production, this should come from iiko.
            iiko_id = f"manual_{index}"
            
            # Check if exists
            stmt = select(Product).where(Product.name_ru == name_ru)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                print(f"Skipping '{name_ru}': already exists")
                continue
                
            new_product = Product(
                iiko_id=iiko_id,
                name_ru=name_ru,
                name_vn=name_vn,
                unit=unit,
                category="Uncategorized"
            )
            session.add(new_product)
            count += 1
            print(f"Prepared '{name_ru}'")
            
        await session.commit()
        print(f"Successfully added {count} products.")

if __name__ == "__main__":
    asyncio.run(main())
