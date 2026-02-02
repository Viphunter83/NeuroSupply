
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

import logging
from src.core.config import settings
from src.services.iiko.client import IikoClient
from src.services.calculation.engine_v2 import CalculationEngineV2
from src.services.order_service import OrderService
from src.db.session import async_session_maker
from src.db.models import User, UserRole

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Registers the user and shows the welcome menu.
    """
    user_id = message.from_user.id
    username = message.from_user.username
    
    async with async_session_maker() as db:
        # Upsert User
        stmt = pg_insert(User).values(
            telegram_id=user_id,
            role=UserRole.COOK # Default role
        ).on_conflict_do_nothing(
            index_elements=['telegram_id']
        )
        await db.execute(stmt)
        await db.commit()
    
    webapp_url = settings.WEBAPP_URL or "http://localhost:5173"
    
    # Simple menu
    kb = [
        [types.KeyboardButton(text="📱 Open Dashboard", web_app=WebAppInfo(url=webapp_url))],
        [types.KeyboardButton(text="📊 Get Report")] 
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        f"Welcome, {username}! You are registered.\nUse the menu below.", 
        reply_markup=keyboard
    )

@router.message(Command("check"))
async def cmd_check_order(message: types.Message):
    """
    Direct link to the dashboard for order checking.
    """
    # Use default or linked restaurant (Future: fetch from DB)
    demo_org_id = settings.IIKO_ORG_ID
    
    base_url = settings.WEBAPP_URL or "http://localhost:5173"
    webapp_url = f"{base_url}?restaurant_id={demo_org_id}"

    kb = [
        [types.InlineKeyboardButton(
            text="Open Dashboard 🚀", 
            web_app=WebAppInfo(url=webapp_url)
        )]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    await message.answer("Click to open the NeuroSupply Dashboard:", reply_markup=keyboard)

@router.message(lambda message: message.text == "📊 Get Report")
@router.message(Command("report"))
async def cmd_report(message: types.Message):
    """
    Manual trigger for the daily report.
    """
    await message.answer("Generating report... ⏳")
    
    # TODO: Connect to NotificationService here to reuse logic
    # For now, just a placeholder or reuse debug logic
    
    try:
        async with async_session_maker() as db:
            engine = CalculationEngineV2(db)
            org_id_str = settings.IIKO_ORG_ID
            
            # Find Rest
            from src.db.models import Restaurant
            res = await db.execute(select(Restaurant).where(Restaurant.iiko_id == org_id_str))
            restaurant = res.scalar_one_or_none()
            
            if not restaurant:
                await message.answer("Error: Restaurant configuration missing.")
                return

            # Calc (Mock Plan 50k)
            # In real Report we should fetch TODAY's plan
            results = await engine.calculate_needs(restaurant.id, 50000.0)
            
            count = len(results)
            total_items = sum(r['quantity'] for r in results)
            
            text = (
                f"<b>Daily Report 📊</b>\n"
                f"Restaurant: {restaurant.name}\n"
                f"Plan: 50,000 ₽\n\n"
                f"Positions to order: {count}\n"
                f"Total Items: {total_items}\n\n"
                f"<i>Open Dashboard for details.</i>"
            )
            
            # Button to Dashboard
            base_url = settings.WEBAPP_URL or "http://localhost:5173"
            webapp_url = f"{base_url}?restaurant_id={org_id_str}"
            
            kb = [[types.InlineKeyboardButton(text="Open Dashboard", web_app=WebAppInfo(url=webapp_url))]]
            
            await message.answer(text, parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
            
    except Exception as e:
        logger.error(f"Report error: {e}")
        await message.answer("Failed to generate report.")
    
# Keep debug_calc for admin usage
@router.message(Command("debug_calc"))
async def cmd_debug_calc(message: types.Message):
    # ... (Keep existing implementation if needed, or remove to clean up)
    await message.answer("Debug command is deprecated. Use /report.")

