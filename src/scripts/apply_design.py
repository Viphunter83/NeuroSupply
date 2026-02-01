
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import argparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "secrets/google_credentials.json"
SHEET_ID = "1mgqHPyqLZsDME4zxEds2XVPdxpVCmhM5zYdbfn62hqM"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return {
        'red': int(hex_color[0:2], 16) / 255.0,
        'green': int(hex_color[2:4], 16) / 255.0,
        'blue': int(hex_color[4:6], 16) / 255.0
    }

COLORS = {
    'header_bg': hex_to_rgb('#4a86e8'),
    'header_text': hex_to_rgb('#ffffff'),
    'editable_bg': hex_to_rgb('#fff2cc'),
    'result_bg': hex_to_rgb('#d9ead3'),
    'result_text': hex_to_rgb('#274e13')
}

def resize_column(ws, col_index, width):
    body = {
        "requests": [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": ws.id,
                        "dimension": "COLUMNS",
                        "startIndex": col_index,
                        "endIndex": col_index + 1
                    },
                    "properties": {
                        "pixelSize": width
                    },
                    "fields": "pixelSize"
                }
            }
        ]
    }
    ws.spreadsheet.batch_update(body)

def apply_design():
    try:
        logger.info("Authenticating...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        
        logger.info(f"Opening Sheet ID: {SHEET_ID}")
        sh = client.open_by_key(SHEET_ID)

        setup_instruction_tab(sh)
        setup_tech_cards(sh)
        setup_forecast(sh)
        setup_product_mix(sh)
        setup_dish_plan(sh)
        setup_draft_order(sh)

        print("\n✅ DESIGN APPLIED SUCCESSFULLY! 🎨")

    except Exception as e:
        logger.error(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

def get_or_create_worksheet(sh, title, rows=100, cols=20):
    try:
        ws = sh.worksheet(title)
        return ws
    except gspread.WorksheetNotFound:
        logger.info(f"Creating tab: {title}")
        return sh.add_worksheet(title=title, rows=rows, cols=cols)

def format_header(ws, cols_count):
    fmt = {
        'backgroundColor': COLORS['header_bg'],
        'textFormat': {'foregroundColor': COLORS['header_text'], 'bold': True, 'fontSize': 10},
        'horizontalAlignment': 'CENTER'
    }
    letter = chr(64 + cols_count) if cols_count <= 26 else 'Z'
    range_name = f"A1:{letter}1"
    ws.format(range_name, fmt)
    ws.freeze(rows=1)

def setup_instruction_tab(sh):
    ws = get_or_create_worksheet(sh, "0. ИНСТРУКЦИЯ ℹ️")
    ws.clear()
    
    content = [
        ["ДОКУМЕНТАЦИЯ СИСТЕМЫ NEUROSUPPLY"],
        [""],
        ["1. КАК ЭТО РАБОТАЕТ"],
        ["Система превращает ваши финансовые планы (Рубли) в конкретные закупки (Кг/Шт)."],
        ["Шаг 1. ПЛАН ПРОДАЖ. Вы ставите фин. цель (например: 500 000 ₽ на точку)."],
        ["Шаг 2. АНАЛИЗ. Система считает кол-во блюд. Проверьте во вкладке '2а. РАСЧЕТ БЛЮД'."],
        ["Шаг 3. РЕЦЕПТЫ. Система берет данные из '1. ТЕХКАРТЫ'."],
        ["Шаг 4. ЗАКАЗ. Готовый список появляется во вкладке '4. ЧЕРНОВИК ЗАКАЗА'."],
        [""],
        ["2. ВАШИ ДЕЙСТВИЯ"],
        ["ЕЖЕДНЕВНО/ЕЖЕНЕДЕЛЬНО:", "Только вкладка '2. ПЛАН ПРОДАЖ'. Это ваш 'руль'."],
        ["РАЗ В МЕСЯЦ (или при смене меню):", "Проверяем '3. ПРОДУКТОВЫЙ МИКС' и '1. ТЕХКАРТЫ'."],
        [""],
        ["3. ЦВЕТОВАЯ ЛЕГЕНДА"],
        ["СИНИЙ ЗАГОЛОВОК", "Названия столбцов (Не менять)"],
        ["ЖЕЛТАЯ ЯЧЕЙКА", "Поле для ВВОДА данных (Вводите цифры здесь)"],
        ["БЕЛАЯ ЯЧЕЙКА", "Справочная информация (Автоматически или редко меняется)"],
        ["ЗЕЛЕНАЯ ЯЧЕЙКА", "ИТОГОВЫЙ РЕЗУЛЬТАТ (Расчет системы)"],
        [""],
        ["🧠 ЛОГИКА СИСТЕМЫ"],
        ["1. ПЛАН ПРОДАЖ (ПЕДАЛЬ ГАЗА)"],
        ["   Вы говорите: «Ждем выручку 500 000 ₽ на ВДНХ»."],
        ["TAB 3. 📊 ПРОДУКТОВЫЙ МИКС (Product Mix) — СТАТИСТИКА"],
        ["   Система помнит: На ВДНХ на каждые 1000₽ выручки обычно приходится 2 Фо Бо и 1 Шейк."],
        ["   (Эти данные подгружаются из iiko. Если вкусы гостей поменялись — статистика обновится)."],
        [""],
        ["TAB 2а. 🍳 РАСЧЕТ БЛЮД (Dish Plan) — ПРОЗРАЧНОСТЬ"],
        ["   Здесь видно, как Деньги превратились в Порции. "],
        ["   Если бот насчитал 200 супов, а вы знаете, что приедет тур. группа — добавьте +50 вручную в столбце 'Коррекция'."],
        [""],
        ["3. ТЕХКАРТЫ (СПРАВОЧНИК)"],
        ["   Система знает: Фо Бо = 150г мяса + 200г лапши."],
        ["ИТОГ: 500 000 ₽ -> Блюда -> Ингредиенты -> Заказ поставщику."],
        [""],
        ["📂 ПУТЕВОДИТЕЛЬ ПО ВКЛАДКАМ"],
        [""],
        ["TAB 2. 📅 ПЛАН ПРОДАЖ (Sales Forecast) — ВАШ ПУЛЬТ УПРАВЛЕНИЯ"],
        ["Что это: Единственное место, где вы говорите системе, сколько продуктов готовить."],
        ["Что делать: Введите прогноз выручки. Изменили выручку — изменился и заказ."],
        [""],
        ["TAB 3. 📊 ПРОДУКТОВЫЙ МИКС (Product Mix) — СТАТИСТИКА"],
        ["Что это: 'Цифровой слепок' спроса вашего ресторана."],
        ["Откуда берется: Выгружается из iiko (Марочный отчет)."],
        ["Зачем вам это: Просто убедиться, что система опирается на верные данные (например, что Фо Бо всё еще хит продаж)."],
        [""],
        ["TAB 1. 🍲 ТЕХКАРТЫ (TechCards) — РЕЦЕПТЫ"],
        ["Что это: Инженерное описание блюд."],
        ["Откуда берется: Из iiko. Если повар изменил закладку мяса — обновите это здесь."],
        [""],
        ["TAB 4. 🛒 ЧЕРНОВИК ЗАКАЗА (Draft Order) — КОРЗИНА"],
        ["Что это: Финальный список для поставщика."],
        ["Фишка: Можно фильтровать по 'Точке' (ресторану)."],
        ["Логика: Округляет граммы до упаковок. Если нужно 1.1 кг сахара — закажет 2 пачки по 1 кг."]
    ]
    
    ws.update(range_name="A1", values=content)
    
    blue = {'red': 0.29, 'green': 0.52, 'blue': 0.91}
    # Styling consistent with previous setup
    ws.format("A1", {'textFormat': {'bold': True, 'fontSize': 14}})
    
    # Bold headers
    for row in [3, 10, 14, 20]:
        ws.format(f"A{row}", {'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': blue}})

    # Tab headers styling (approx locations)
    # Since content length is variable, strict formatting by index is fragile, but sufficient for this script.
    
    try:
        resize_column(ws, 0, 600)
    except: pass

def setup_tech_cards(sh):
    titles = ["1. TechCards", "1. ТЕХКАРТЫ 🍲"]
    ws = get_or_create_worksheet(sh, titles[1]) 
    try:
        old_ws = sh.worksheet(titles[0])
        if old_ws.title != titles[1]:
            old_ws.update_title(titles[1])
            ws = old_ws
    except: pass

    headers = ["Блюдо / Полуфабрикат", "Ингредиент", "Брутто (Кол-во)", "Ед. изм.", "Нетто", "Комментарий"]
    existing = ws.get("A1:A1")
    if not existing:
        ws.update(range_name="A1", values=[headers])
    else:
        # Check if headers match roughly, if not overwrite? Better overwrite headers to enforce design
        ws.update(range_name="A1:F1", values=[headers])

    format_header(ws, len(headers))
    ws.format("C2:C1000", {'backgroundColor': COLORS['editable_bg']})
    
    try:
        resize_column(ws, 0, 200)
        resize_column(ws, 1, 200)
        resize_column(ws, 2, 100)
        resize_column(ws, 5, 300)
    except: pass

def setup_forecast(sh):
    titles = ["2. Sales Forecast", "2. ПЛАН ПРОДАЖ 📅"]
    ws = get_or_create_worksheet(sh, titles[1])
    try:
        old = sh.worksheet(titles[0])
        old.update_title(titles[1])
        ws = old
    except: pass

    headers = ["Период (Месяц/Неделя)", "Точка (Ресторан)", "Прогноз Выручки (₽)", "Комментарий"]
    ws.update(range_name="A1:D1", values=[headers])
    format_header(ws, len(headers))
    ws.format("C2:C1000", {'backgroundColor': COLORS['editable_bg'], 'numberFormat': {'type': 'CURRENCY', 'pattern': '#,##0 ₽'}})
    try: resize_column(ws, 2, 150)
    except: pass

def setup_dish_plan(sh):
    titles = ["2a. Dish Plan", "2а. РАСЧЕТ БЛЮД 🍳"]
    ws = get_or_create_worksheet(sh, titles[1])
    try:
        old = sh.worksheet(titles[0])
        old.update_title(titles[1])
        ws = old
    except: pass

    headers = ["Точка (Ресторан)", "Блюдо", "Авто-Прогноз (Шт)", "Коррекция (+/-)", "ИТОГ К ЗАКАЗУ (Шт)"]
    ws.update(range_name="A1:E1", values=[headers])
    format_header(ws, len(headers))
    
    # Yellow: D (Correction)
    ws.format("D2:D1000", {'backgroundColor': COLORS['editable_bg']})
    # Green result: E
    ws.format("E2:E1000", {'backgroundColor': COLORS['result_bg'], 'textFormat': {'foregroundColor': COLORS['result_text'], 'bold': True}})
    
    # Gray auto: C
    ws.format("C2:C1000", {'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})

    try:
        resize_column(ws, 0, 150) # Outlet
        resize_column(ws, 1, 250) # Dish
        resize_column(ws, 2, 150) # Auto
        resize_column(ws, 3, 150) # Correction
        resize_column(ws, 4, 150) # Final
    except: pass

def setup_product_mix(sh):
    titles = ["3. Product Mix", "3. ПРОДУКТОВЫЙ МИКС 📊"]
    ws = get_or_create_worksheet(sh, titles[1])
    try:
        old = sh.worksheet(titles[0])
        old.update_title(titles[1])
        ws = old
    except: pass

    # Added "Точка" as first column
    headers = ["Точка (Ресторан)", "Блюдо", "Категория", "Доля в выручке (%)", "Средняя цена (₽)", "Расчетное кол-во (справочно)"]
    ws.update(range_name="A1:F1", values=[headers])
    format_header(ws, len(headers))
    
    # Yellow: D (Share), E (Price)
    ws.format("D2:D1000", {'backgroundColor': COLORS['editable_bg'], 'numberFormat': {'type': 'PERCENT', 'pattern': '0.00%'}})
    ws.format("E2:E1000", {'backgroundColor': COLORS['editable_bg'], 'numberFormat': {'type': 'CURRENCY', 'pattern': '#,##0 ₽'}})
    
    try:
        resize_column(ws, 0, 150) # Outlet
        resize_column(ws, 1, 250) # Name
    except: pass

def setup_draft_order(sh):
    titles = ["4. DRAFT ORDER", "4. ЧЕРНОВИК ЗАКАЗА 🛒"]
    ws = get_or_create_worksheet(sh, titles[1])
    try:
        old = sh.worksheet(titles[0])
        old.update_title(titles[1])
        ws = old
    except: pass

    # Added "Точка" as first column
    # Added "Склад (Остаток)" column before Final Order
    headers = ["Точка (Ресторан)", "Ингредиент", "Потребность (Сырье)", "Ед. изм.", "Склад (Остаток)", "Упаковка (Размер)", "К ЗАКАЗУ (Шт/Упак)", "Ед. Заказа", "Логика / Комментарий"]
    ws.update(range_name="A1:I1", values=[headers])
    format_header(ws, len(headers))
    
    # Yellow: E (Stock)
    ws.format("E2:E1000", {'backgroundColor': COLORS['editable_bg']})

    # Green Result: G (Order Qty)
    ws.format("G2:G1000", {'backgroundColor': COLORS['result_bg'], 'textFormat': {'foregroundColor': COLORS['result_text'], 'bold': True}})
    
    try:
        resize_column(ws, 0, 150) # Outlet
        resize_column(ws, 1, 200) # Ing
        resize_column(ws, 6, 150) # Order Qty
        resize_column(ws, 8, 300) # Logic
    except: pass

if __name__ == "__main__":
    apply_design()
