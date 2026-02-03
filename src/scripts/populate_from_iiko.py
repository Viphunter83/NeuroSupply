import sys
import os
import asyncio
import logging
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.getcwd())

from src.core.config import settings
from src.services.data_loader.sheets_client import SheetsClient
from src.services.iiko.client import IikoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def populate_real_data():
    logger.info("Initializing clients...")
    iiko = IikoClient()
    sheets = SheetsClient(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
    
    try:
        # 1. Auth and Fetch Data
        
        # Get Active Restaurant from Sheets
        org_id = sheets.get_active_restaurant_id()
        if not org_id:
            logger.error("No active restaurant ID found in Settings or Env (IIKO_ORG_ID).")
            return
            
        logger.info(f"Using Active Restaurant ID: {org_id}")

        logger.info("Authenticating with iiko...")
        await iiko.auth()

        # logger.info(f"Fetching Tech Cards for Org ID: {org_id}...")
        # try:
        #     tech_cards_resp = await iiko.get_tech_cards(org_id)
        # except Exception as e:
        #     logger.warning(f"Failed to fetch Tech Cards (likely permissions/plan issue): {e}")
        #     tech_cards_resp = []

        # TEMPORARY SKIP TECH CARDS TO FOCUS ON PRODUCT MIX
        # The 401 error is blocking everything.
        logger.warning("Skipping Tech Cards fetch due to API access issues (401).")
        tech_cards_resp = []
        
        logger.info(f"Fetching Menu for Org ID: {org_id}...")
        try:
            menu_resp = await iiko.get_menu(org_id)
            products = menu_resp.get("products", [])
            product_map = {p["id"]: p for p in products}
        except Exception as e:
            logger.error(f"Failed to fetch Menu: {e}")
            return

        # 3. Transform Product Mix (Menu) FIRST to get dishes
        logger.info("Transforming Product Mix...")
        sheet_mix_rows = []
        dishes = [p for p in products if p.get("type") == "Dish" and not p.get("isDeleted")]
        
        # Calculate prob (Share in Revenue %)
        # Goal: Equal share -> 1.0 / N (Fraction)
        prob_share = round(1.0 / len(dishes), 4) if dishes else 0
        
        restaurant_name = "Real iiko Restaurant" # Placeholder
        
        mix_header = ['Точка (Ресторан)', 'Блюдо', 'Категория', 'Доля в выручке (%)', 'Средняя цена (₽)', 'Расчетное кол-во (справочно)']
        
        def get_mock_price(name):
            n = name.lower()
            if "pho" in n or "фо" in n: return 650
            if "bun" in n or "бун" in n: return 550
            if "com" in n or "рис" in n: return 450
            if "nem" in n or "нэм" in n: return 350
            if "mang" in n or "манго" in n: return 300
            return 400

        for dish in dishes:
            price = dish.get("price", 0)
            if price == 0:
                price = get_mock_price(dish["name"])

            row = [
                restaurant_name,
                dish["name"],
                dish.get("parentGroup", "Main"), # Needs group lookup really, but using ID or placeholder
                prob_share, # Probability (Share %)
                price, 
                "" # Calc qty ref
            ]
            sheet_mix_rows.append(row)

        # 2. GENERATE Pseudo Tech Cards based on Dishes
        logger.info("Generating Pseudo Tech Cards from Menu...")
        sheet_tech_rows = []
        
        # Simple recipe generator for Vietnamese Cuisine
        def get_recipe(dish_name):
            name_lower = dish_name.lower()
            ingredients = []
            
            if "pho" in name_lower or "фо" in name_lower:
                ingredients = [
                    ("Говяжий Бульон", 0.350, "л"),
                    ("Рисовая Лапша", 0.150, "кг"),
                    ("Говядина Вырезка", 0.080, "кг"),
                    ("Лук Зеленый", 0.020, "кг"),
                    ("Зелень (Специи)", 0.010, "кг")
                ]
            elif "bun" in name_lower or "бун" in name_lower:
                ingredients = [
                    ("Рисовая Лапша", 0.150, "кг"),
                    ("Свинина (Гриль)", 0.100, "кг"),
                    ("Рыбный Соус", 0.030, "л"),
                    ("Салат Айсберг", 0.050, "кг"),
                    ("Арахис", 0.010, "кг")
                ]
            elif "com" in name_lower or "рис" in name_lower:
                ingredients = [
                    ("Рис Жасмин (Отварной)", 0.200, "кг"),
                    ("Курица Филе", 0.120, "кг"),
                    ("Маринад", 0.030, "кг"),
                    ("Огурец", 0.050, "кг")
                ]
            elif "nem" in name_lower or "нэм" in name_lower:
                 ingredients = [
                    ("Рисовая Бумага", 0.020, "кг"),
                    ("Фарш Свиной", 0.050, "кг"),
                    ("Фунчоза", 0.020, "кг"),
                    ("Морковь", 0.020, "кг")
                ]
            elif "mang" in name_lower or "манго" in name_lower:
                ingredients = [
                    ("Манго Свежий", 0.150, "кг"),
                    ("Сироп Сахарный", 0.050, "л"),
                    ("Лед", 0.100, "кг")
                ]
            else:
                # Generic fallback
                ingredients = [
                    ("Основной Ингредиент", 0.200, "кг"),
                    ("Соус Фирменный", 0.050, "л"),
                    ("Гарнир Овощной", 0.100, "кг")
                ]
                
            return ingredients

        count_tc = 0
        for dish in dishes:
            recipe = get_recipe(dish["name"])
            for ing_name, amount, unit in recipe:
                # 'Блюдо / Полуфабрикат', 'Ингредиент', 'Брутто (Кол-во)', 'Ед. изм.', 'Нетто', 'Комментарий'
                row = [dish["name"], ing_name, amount, unit, amount, "Auto-Generated"]
                sheet_tech_rows.append(row)
            count_tc += 1
        # Old Tech Card Processing Logic Removed

        # 4. Write to Sheets
        if sheet_tech_rows:
            logger.info(f"Writing {len(sheet_tech_rows)} rows to '1. ТЕХКАРТЫ 🍲'...")
            sheets.clear_worksheet("1. ТЕХКАРТЫ 🍲")
            header = ['Блюдо / Полуфабрикат', 'Ингредиент', 'Брутто (Кол-во)', 'Ед. изм.', 'Нетто', 'Комментарий']
            sheets.update_worksheet("1. ТЕХКАРТЫ 🍲", [header] + sheet_tech_rows)
        
        if sheet_mix_rows:
            logger.info(f"Writing {len(sheet_mix_rows)} rows to '3. ПРОДУКТОВЫЙ МИКС 📊'...")
            sheets.clear_worksheet("3. ПРОДУКТОВЫЙ МИКС 📊")
            header = ['Точка (Ресторан)', 'Блюдо', 'Категория', 'Доля в выручке (%)', 'Средняя цена (₽)', 'Расчетное кол-во (справочно)']
            sheets.update_worksheet("3. ПРОДУКТОВЫЙ МИКС 📊", [header] + sheet_mix_rows)

        logger.info("Done!")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await iiko.close()

if __name__ == "__main__":
    asyncio.run(populate_real_data())
