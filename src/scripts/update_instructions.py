
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "secrets/google_credentials.json"
SHEET_ID = "1mgqHPyqLZsDME4zxEds2XVPdxpVCmhM5zYdbfn62hqM"

def update_instructions():
    try:
        logger.info("Authenticating...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("0. ИНСТРУКЦИЯ ℹ️")

        logger.info("Updating instruction content...")
        
        # Define detailed, friendly content
        content = [
            ["🤖 ДОБРО ПОЖАЛОВАТЬ В NEUROSUPPLY OS"],
            [""],
            ["👋 Привет! Я — искусственный интеллект, который помогает вашему ресторану заказывать продукты."],
            ["Моя цель: чтобы на кухне всегда всего хватало, а списаний было ноль."],
            ["Ниже — простая инструкция, как мы будем работать вместе."],
            [""],
            ["🧠 КАК ДУМАЕТ СИСТЕМА (ЛОГИКА)"],
            ["Я не умею гадать, но я умею отлично считать. Мой расчет строится на 3-х китах:"],
            ["1. СКОЛЬКО ДЕНЕГ? (План Продаж)"],
            ["   Мы говорим системе: «В пятницу ждем выручку 500 000 ₽»."],
            ["2. ЧТО КУПЯТ? (Продуктовый Микс)"],
            ["   Система знает статистику: на 500 тыс обычно берут 200 порций Фо Бо и 300 Манго-шейков."],
            ["3. ИЗ ЧЕГО ЭТО СОСТОИТ? (Техкарты)"],
            ["   Система знает: 1 Фо Бо = 0.15 кг говядины + 0.2 кг рисовой лапши."],
            ["ИТОГ: Система умножает планы на микс и на рецепты -> и получает точный список закупки."],
            [""],
            ["📂 ПУТЕВОДИТЕЛЬ ПО ВКЛАДКАМ"],
            [""],
            ["TAB 2. 📅 ПЛАН ПРОДАЖ (Sales Forecast) — ВАШ ПУЛЬТ УПРАВЛЕНИЯ"],
            ["Что это: Единственное место, где вы управляете объемом заказа."],
            ["Что делать: Введите прогноз выручки по каждой точке на период."],
            ["Совет: Если ожидаете банкет или праздник — просто увеличьте сумму выручки, заказ пересчитается сам."],
            ["Поля: 🟡 Желтые ячейки — для цифр. 🔵 Синие — не трогаем."],
            [""],
            ["TAB 3. 📊 ПРОДУКТОВЫЙ МИКС (Product Mix) — МОЗГ СИСТЕМЫ"],
            ["Что это: Статистика ваших продаж. Она превращает Деньги (₽) в Блюда (Шт)."],
            ["Что делать: Обычно заполняется раз в месяц (или загружается из iiko)."],
            ["Логика: Если 'Доля в выручке' Фо Бо 10%, то из 100 руб выручки — 10 руб мы отдаем за суп."],
            ["Важно: Сумма всех долей (%) должна быть равна 100%."],
            [""],
            ["TAB 1. 🍲 ТЕХКАРТЫ (TechCards) — СПРАВОЧНИК"],
            ["Что это: База знаний о составе блюд."],
            ["Что делать: Загружаем сюда рецепты из iiko. Если поменяли рецепт — обновите здесь."],
            ["Важно: Названия блюд здесь и в 'Продуктовом Миксе' должны совпадать буква в букву!"],
            [""],
            ["TAB 4. 🛒 ЧЕРНОВИК ЗАКАЗА (Draft Order) — РЕЗУЛЬТАТ"],
            ["Что это: Готовый список покупок, который я посчитал."],
            ["Что делать: Проверьте глазами. Если всё ок — можно отправлять поставщику."],
            ["Логика: Я округляю граммы до целых упаковок (если знаем размер упаковки)."],
            [""],
            ["🎨 ЦВЕТОВАЯ ЛЕГЕНДА"],
            ["🔵 СИНИЙ ЗАГОЛОВОК", "Это структура таблицы. Не меняйте названия столбцов и не удаляйте их."],
            ["🟡 ЖЕЛТАЯ ЯЧЕЙКА", "🖊️ ВВОД ДАННЫХ. Сюда пишите вы (планы, цены, проценты)."],
            ["⚪ БЕЛАЯ ЯЧЕЙКА", "👁️ ТОЛЬКО ЧТЕНИЕ. Рассчитывается автоматически или это справочник."],
            ["🟢 ЗЕЛЕНАЯ ЯЧЕЙКА", "✅ РЕЗУЛЬТАТ. То, ради чего всё затевалось (сколько заказать)."],
            [""],
            ["❓ ЧАСТЫЕ ВОПРОСЫ"],
            ["В: Я добавил новое блюдо, почему его нет в заказе?"],
            ["О: Проверьте: 1) Есть ли на него Техкарта? 2) Есть ли оно в Продуктовом Миксе?"],
            ["В: Почему заказ кажется слишком большим?"],
            ["О: Проверьте План Продаж (не лишний ли нолик?) и Техкарты (может, там кг вместо г?)."]
        ]
        
        ws.clear()
        ws.update(range_name="A1", values=content)
        
        # Styling
        blue = {'red': 0.29, 'green': 0.52, 'blue': 0.91}
        yellow = {'red': 1.0, 'green': 0.95, 'blue': 0.8}
        green = {'red': 0.85, 'green': 0.92, 'blue': 0.83}
        
        # Headers
        ws.format("A1", {"textFormat": {"bold": True, "fontSize": 16}})
        
        # Subheaders
        subheader_format = {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": blue}}
        ws.format("A7", subheader_format)
        ws.format("A17", subheader_format)
        ws.format("A39", subheader_format)
        ws.format("A45", subheader_format)
        
        # Tab Headers
        tab_header_fmt = {"backgroundColor": blue, "textFormat": {"foregroundColor": {"red":1,"green":1,"blue":1}, "bold": True}}
        ws.format("A19", tab_header_fmt)
        ws.format("A24", tab_header_fmt)
        ws.format("A30", tab_header_fmt)
        ws.format("A34", tab_header_fmt)
        
        # Legend
        ws.format("A40", {"backgroundColor": blue, "textFormat": {"foregroundColor": {"red":1,"green":1,"blue":1}}})
        ws.format("A41", {"backgroundColor": yellow})
        ws.format("A43", {"backgroundColor": green})
        
        # Column width
        ws.spreadsheet.batch_update({
            "requests": [{"updateDimensionProperties": {
                "range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 600},
                "fields": "pixelSize"
            }}]
        })

        print("\n✅ New Friendly Instructions Uploaded!")

    except Exception as e:
        logger.error(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_instructions()
