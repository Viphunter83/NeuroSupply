import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.getcwd())

from src.core.config import settings
from src.services.data_loader.sheets_client import SheetsClient

def run_sync():
    print("--- 1. CONFIG VERIFICATION ---")
    print(f"Credentials Path: {settings.GOOGLE_SHEETS_CREDENTIALS_PATH}")
    print(f"Spreadsheet ID: {settings.GOOGLE_SHEETS_SPREADSHEET_ID}")
    
    client = SheetsClient()
    print("✅ Client initialized.")

    print("\n--- 2. CONNECTION TEST (Reading '2. ПЛАН ПРОДАЖ 📅') ---")
    try:
        sheet = client.client.open_by_key(client.sheet_id)
        sales_ws = sheet.worksheet("2. ПЛАН ПРОДАЖ 📅")
        sales_data = sales_ws.get_all_values()
        if len(sales_data) > 1:
            print(f"✅ Success! Read {len(sales_data)} rows. First row: {sales_data[0]}")
        else:
            print("⚠️ Connected, but sheet seems empty or only has header.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    print("\n--- 3. POPULATING '1. ТЕХКАРТЫ' ---")
    tech_cards_header = ['Блюдо / Полуфабрикат', 'Ингредиент', 'Брутто (Кол-во)', 'Ед. изм.', 'Нетто', 'Комментарий']
    tech_cards_data = [
        # Borscht
        ['Борщ', 'Говядина', '0.150', 'кг', '0.120', ''],
        ['Борщ', 'Свекла', '0.200', 'кг', '0.180', ''],
        ['Борщ', 'Картофель', '0.100', 'кг', '0.080', ''],
        ['Борщ', 'Капуста', '0.100', 'кг', '0.090', ''],
        # Carbonara
        ['Паста Карбонара', 'Спагетти', '0.100', 'кг', '0.100', ''],
        ['Паста Карбонара', 'Бекон', '0.050', 'кг', '0.050', ''],
        ['Паста Карбонара', 'Сливки 33%', '0.080', 'л', '0.080', ''],
        ['Паста Карбонара', 'Пармезан', '0.020', 'кг', '0.020', ''],
        # Burger
        ['Бургер Классический', 'Булка для бургера', '1', 'шт', '1', ''],
        ['Бургер Классический', 'Котлета говяжья', '1', 'шт', '1', ''],
        ['Бургер Классический', 'Томат', '0.030', 'кг', '0.030', ''],
        ['Бургер Классический', 'Лист салата', '0.010', 'кг', '0.010', ''],
        ['Бургер Классический', 'Соус Бургер', '0.020', 'кг', '0.020', ''],
    ]
    
    client.clear_worksheet("1. ТЕХКАРТЫ 🍲")
    client.update_worksheet("1. ТЕХКАРТЫ 🍲", [tech_cards_header] + tech_cards_data)
    print("✅ Tech Cards Populated.")

    print("\n--- 4. POPULATING '3. ПРОДУКТОВЫЙ МИКС 📊' ---")
    # Need to find a valid Restaurant ID/Name from Sales Plan to link mix
    # Assuming 'VDNH' or similar exists in Sales Plan, let's look at what we read earlier
    # sales_data[1][0] is usually the first row's first column.
    
    # For now, we will add generic mix data. The system links by Name usually or ID.
    # Headers: ['Точка (Ресторан)', 'Блюдо', 'Категория', 'Доля в выручке (%)', 'Средняя цена (₽)', 'Расчетное кол-во (справочно)']
    
    # We will use 'Global' or the first one found in Sales Plan to make it somewhat realistic if possible, 
    # but hardcoded 'VDNH' (or whatever is in the sales plan) is safer if valid.
    # Let's check sales plan data first 5 rows to pick a restaurant name.
    
    restaurant_name = "SomeRestaurant"
    if len(sales_data) > 1:
         # Column B is Restaurant Name (Index 1)
        restaurant_name = sales_data[1][1] 
        print(f"Using Restaurant Name from Sales Plan: {restaurant_name}")

    mix_header = ['Точка (Ресторан)', 'Блюдо', 'Категория', 'Доля в выручке (%)', 'Средняя цена (₽)', 'Расчетное кол-во (справочно)']
    mix_data = [
        [restaurant_name, 'Борщ', 'Супы', '15', '450', ''],
        [restaurant_name, 'Паста Карбонара', 'Горячее', '20', '550', ''],
        [restaurant_name, 'Бургер Классический', 'Бургеры', '25', '650', ''],
        [restaurant_name, 'Кофе', 'Напитки', '30', '250', ''], # Item without tech card to test partial data
    ]

    client.clear_worksheet("3. ПРОДУКТОВЫЙ МИКС 📊")
    client.update_worksheet("3. ПРОДУКТОВЫЙ МИКС 📊", [mix_header] + mix_data)
    print(f"✅ Product Mix Populated for '{restaurant_name}'.")

    print("\n--- DONE ---")

if __name__ == "__main__":
    run_sync()
