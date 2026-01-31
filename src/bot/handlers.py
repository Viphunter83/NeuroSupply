
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

import logging
from src.core.config import settings
from src.services.iiko.client import IikoClient
from src.services.calculation.engine import CalculationEngine
from src.services.order_service import OrderService
from src.db.session import async_session_maker

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    webapp_url = settings.WEBAPP_URL or "https://google.com" 
    kb = [
        [types.KeyboardButton(text="Open NeuroSupply", web_app=WebAppInfo(url=webapp_url))]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Welcome to NeuroSupply! Click below to open.", reply_markup=keyboard)

@router.message(Command("check"))
async def cmd_check_order(message: types.Message):
    """
    Check for the latest draft order and offer confirmation via WebApp.
    """
    demo_org_id = settings.IIKO_ORG_ID
    if not demo_org_id:
         await message.answer("Error: Org ID not configured.")
         return

    # Construct WebApp URL with query param
    # Make sure WEBAPP_URL is set in .env, e.g. http://localhost:3000
    base_url = settings.WEBAPP_URL or "http://localhost:3000"
    webapp_url = f"{base_url}?restaurant_id={demo_org_id}"

    kb = [
        [types.KeyboardButton(
            text="Открыть заказ / Mở đơn hàng", 
            web_app=WebAppInfo(url=webapp_url)
        )]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer("Click the button below to review and confirm the order:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_order:"))
async def process_confirm_callback(callback_query: types.CallbackQuery):
    order_id_str = callback_query.data.split(":")[1]
    
    await callback_query.answer("Confirming order...")
    
    async with async_session_maker() as db:
        service = OrderService(db)
        try:
            import uuid
            o_id = uuid.UUID(order_id_str)
            confirmed_order = await service.confirm_order(o_id)
            
            await callback_query.message.edit_text(
                f"✅ <b>Order Confirmed!</b>\n\nOrder {confirmed_order.id} has been verified and sent to processing.",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.exception("Error confirming order")
            await callback_query.message.answer(f"Error confirming order: {str(e)}")

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
