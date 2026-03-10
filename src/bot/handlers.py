
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
    Registers the user and shows the role-based welcome menu.
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
        
        # Fetch user to get their role and linked restaurant
        stmt_user = select(User).where(User.telegram_id == user_id)
        result = await db.execute(stmt_user)
        user = result.scalar_one_or_none()
        role = user.role if user else UserRole.COOK
        linked_rest_id = user.linked_restaurant_id if user else None
    
    webapp_url = settings.WEBAPP_URL or "http://localhost:5173"
    # Ensure URL ends without trailing slash and point to /dashboard
    webapp_url = webapp_url.rstrip('/')
    dashboard_url = f"{webapp_url}/dashboard"
    
    kb = []
    if role == UserRole.COOK:
        # Cook Menu (Zero-UI inventory check)
        url = f"{webapp_url}?restaurant_id={linked_rest_id}" if linked_rest_id else webapp_url
        kb.append([types.KeyboardButton(text="📝 Инвентаризация (Kiểm tra kho)", web_app=WebAppInfo(url=url))])
        
        if not linked_rest_id:
            welcome_text = (
                f"Добро пожаловать, {username}!\n\n"
                "⚠️ Вы не привязаны к ресторану. Пожалуйста, обратитесь к администратору.\n"
                "Admin ID для привязки: `" + str(user_id) + "`"
            )
        else:
            welcome_text = f"Добро пожаловать, {username}!\nНажмите кнопку ниже, чтобы провести инвентаризацию."
            
    elif role == UserRole.MANAGER:
        # Manager Menu
        manager_app_url = f"{dashboard_url}/orders?restaurant_id={linked_rest_id}" if linked_rest_id else dashboard_url
        kb.append([types.KeyboardButton(text="📦 Панель управления (Dashboard)", web_app=WebAppInfo(url=manager_app_url))])
        kb.append([types.KeyboardButton(text="📊 Дневной Отчет")])
        welcome_text = f"Добро пожаловать, {username}! (Менеджер)\nВыберите действие в меню."
    else:
        # Admin Menu
        kb.append([types.KeyboardButton(text="🚀 Открыть Дашборд", web_app=WebAppInfo(url=dashboard_url))])
        kb.append([types.KeyboardButton(text="📊 Дневной Отчет")])
        kb.append([types.KeyboardButton(text="⚙️ Настройки"), types.KeyboardButton(text="🛠 Принудительный расчет")])
        welcome_text = (
            f"Добро пожаловать, {username}! (Администратор)\n\n"
            "Вы можете использовать команду /link [user_id] [restaurant_uuid] для привязки пользователей."
        )
        
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(Command("link"))
async def cmd_link(message: types.Message):
    """
    Command for admins to link users to restaurants.
    Format: /link <user_id> <restaurant_uuid>
    """
    user_id = message.from_user.id
    
    async with async_session_maker() as db:
        # Check if requester is Admin
        stmt = select(User).where(User.telegram_id == user_id)
        result = await db.execute(stmt)
        admin_user = result.scalar_one_or_none()
        
        if not admin_user or admin_user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет прав администратора.")
            return
            
        args = message.text.split()
        if len(args) != 3:
            # Try to list restaurants if args are missing
            from src.db.models import Restaurant
            res_list = await db.execute(select(Restaurant))
            restaurants = res_list.scalars().all()
            
            rest_text = "\n".join([f"• `{r.id}` - {r.name}" for r in restaurants])
            await message.answer(
                "Использование: `/link <user_id> <restaurant_uuid>`\n\n"
                "Список ресторанов:\n" + rest_text,
                parse_mode="Markdown"
            )
            return
            
        target_user_id = int(args[1])
        target_rest_uuid = args[2]
        
        try:
            import uuid
            rest_uuid = uuid.UUID(target_rest_uuid)
            
            # Update user
            from sqlalchemy import update
            stmt_update = update(User).where(User.telegram_id == target_user_id).values(linked_restaurant_id=rest_uuid)
            await db.execute(stmt_update)
            await db.commit()
            
            await message.answer(f"✅ Пользователь `{target_user_id}` привязан к ресторану `{target_rest_uuid}`.", parse_mode="Markdown")
        except ValueError:
            await message.answer("❌ Неверный формат UUID.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("check"))
async def cmd_check_order(message: types.Message):
    """
    Direct link to the dashboard for order checking.
    """
    base_url = settings.WEBAPP_URL or "http://localhost:5173"
    base_url = base_url.rstrip('/')
    dashboard_url = f"{base_url}/dashboard"
    
    async with async_session_maker() as db:
        from src.db.models import Restaurant
        result = await db.execute(select(Restaurant))
        restaurants = result.scalars().all()
    
    if not restaurants:
        await message.answer("No restaurants configured.")
        return

    # If only one, show directly
    if len(restaurants) == 1:
        r = restaurants[0]
        # Use v=2 and restaurant_id for legacy support if needed, or just dashboard
        webapp_url = f"{dashboard_url}/orders?restaurant_id={r.id}"
        kb = [[types.InlineKeyboardButton(text=f"Open {r.name} 🚀", web_app=WebAppInfo(url=webapp_url))]]
        await message.answer(f"Dashboard for {r.name}:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
    else:
        # Show list
        kb = []
        for r in restaurants:
            webapp_url = f"{dashboard_url}/orders?restaurant_id={r.id}"
            kb.append([types.InlineKeyboardButton(text=f"Open {r.name}", web_app=WebAppInfo(url=webapp_url))])
        
        await message.answer("Select Restaurant to manage:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))


@router.message(lambda message: message.text == "📊 Дневной Отчет" or message.text == "📊 Get Report")
@router.message(Command("report"))
async def cmd_report(message: types.Message):
    """
    Manual trigger for the daily report. Restricted to MANAGER and ADMIN.
    """
    async with async_session_maker() as db:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or user.role == UserRole.COOK:
            await message.answer("⚠️ У вас нет прав для выполнения этой команды.")
            return

    await message.answer("Generating report... ⏳")
    
    try:
        async with async_session_maker() as db:
            from src.db.models import Restaurant
            result = await db.execute(select(Restaurant))
            restaurants = result.scalars().all()
            
            if not restaurants:
                await message.answer("Error: No restaurants found in DB.")
                return

            # For now, if multiple, report ALL (or we could ask user)
            # Simplification: Loop through all and report
            
            base_url = settings.WEBAPP_URL or "http://localhost:5173"
            
            for restaurant in restaurants:
                engine = CalculationEngineV2(db)
                
                # Fetch today's Sales Plan from DB
                from src.db.models import SalesPlan
                from datetime import date
                plan_stmt = select(SalesPlan).where(
                    SalesPlan.restaurant_id == restaurant.id,
                    SalesPlan.date == date.today()
                )
                plan_res = await db.execute(plan_stmt)
                plan = plan_res.scalar_one_or_none()
                plan_amount = float(plan.amount_rub) if plan else 0.0
                
                if plan_amount <= 0:
                    await message.answer(f"⚠️ Нет плана продаж на сегодня для {restaurant.name}.")
                    continue
                
                items, _ = await engine.calculate_needs(restaurant.id, plan_amount)
                
                count = len(items)
                total_items = sum(r['quantity'] for r in items)
                
                text = (
                    f"<b>Daily Report 📊</b>\n"
                    f"Restaurant: {restaurant.name}\n"
                    f"Plan: {plan_amount:,.0f} ₽\n\n"
                    f"Positions to order: {count}\n"
                    f"Total Items: {total_items}\n"
                )
                
                webapp_url = f"{base_url}?view=manager&restaurant_id={restaurant.iiko_id}&v=2"
                kb = [[types.InlineKeyboardButton(text=f"Open {restaurant.name}", web_app=WebAppInfo(url=webapp_url))]]
                
                await message.answer(text, parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
            
    except Exception as e:
        logger.error(f"Report error: {e}")
        await message.answer(f"Failed to generate report: {e}")
    
# Keep debug_calc for admin usage
@router.message(Command("debug_calc"))
async def cmd_debug_calc(message: types.Message):
    # ... (Keep existing implementation if needed, or remove to clean up)
    await message.answer("Debug command is deprecated. Use /report.")

