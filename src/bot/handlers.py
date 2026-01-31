
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.iiko.client import IikoClient
from src.services.calculation.engine import CalculationEngine
from src.db.session import async_session_maker

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    webapp_url = settings.WEBAPP_URL or "https://google.com" 
    kb = [
        [types.KeyboardButton(text="Open NeuroSupply", web_app=WebAppInfo(url=webapp_url))]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Welcome to NeuroSupply! Click below to open.", reply_markup=keyboard)

@router.message(Command("debug_calc"))
async def cmd_debug_calc(message: types.Message):
    await message.answer("Starting calculation... Please wait.")
    
    try:
        # Initialize services
        iiko = IikoClient()
        await iiko.auth()
        
        async with async_session_maker() as db:
            engine = CalculationEngine(iiko, db)
            
            # Use Org ID from settings or env
            # settings.IIKO_ORG_ID might not be defined if I didn't update config.py
            # Fallback to os.getenv if needed, but config is better.
            org_id = settings.IIKO_ORG_ID
            
            if not org_id:
                await message.answer("Error: IIKO_ORG_ID is not set in configuration.")
                return

            results = await engine.calculate_order(org_id)
            
        # Format results
        if not results:
            await message.answer("Calculation completed. No orders recommended (or no data).")
            return
            
        response = ["<b>Calculation Results:</b>"]
        for item in results:
            line = f"• {item['product_name']}: {item['order_qty']} {item['unit']} (Pred: {item['predicted_kg']:.2f}, Stock: {item['stock']})"
            response.append(line)
            
        # Split message if too long (Telegram limit 4096)
        text = "\n".join(response)
        if len(text) > 4000:
             text = text[:4000] + "\n... (truncated)"
             
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"Error during calculation: {str(e)}")
    finally:
        # Ensure iiko client is closed
        if 'iiko' in locals():
            await iiko.close()
