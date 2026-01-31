
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
    Check for the latest draft order and offer confirmation.
    """
    await message.answer("Checking for draft orders...")
    
    # Needs to know Restaurant ID. 
    # For MVP, hardcode or fetch from User mapping.
    # We will use the VDNH ID for demo.
    demo_org_id = settings.IIKO_ORG_ID 
    if not demo_org_id:
         await message.answer("Error: Org ID not configured.")
         return

    async with async_session_maker() as db:
        service = OrderService(db)
        try:
            # We need to convert string settings ID to UUID if needed, 
            # but OrderService expects UUID.
            import uuid
            r_id = uuid.UUID(demo_org_id)
            order = await service.get_latest_draft_order(r_id)
            
            if not order:
                await message.answer("No draft orders found for this restaurant.")
                return
                
            # Format Order
            text = f"📋 <b>Draft Order Found!</b>\n"
            text += f"ID: <code>{order.id}</code>\n"
            text += f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            text += f"Items: {len(order.items)}\n\n"
            
            # Show top 5 items
            for i, item in enumerate(order.items[:5]):
                text += f"{i+1}. {item['product_name']} - {item['quantity']} {item['unit']}\n"
            
            if len(order.items) > 5:
                text += f"... and {len(order.items) - 5} more items."
                
            # Add Confirm Button
            kb = [
                [types.InlineKeyboardButton(text="✅ Confirm Order", callback_data=f"confirm_order:{order.id}")]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            
        except Exception as e:
            logger.exception("Error checking order")
            await message.answer(f"Error: {str(e)}")


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
