"""
API Dependencies: Authentication, Authorization, DB Session.
"""

import hashlib
import hmac
import json
import logging
import urllib.parse
import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models.restaurant import Restaurant
from src.db.models.user import User, UserRole
from src.db.session import async_session_maker

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# DB Session
# ──────────────────────────────────────────────

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# ──────────────────────────────────────────────
# Telegram initData HMAC Validation
# ──────────────────────────────────────────────

def _validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validates Telegram WebApp initData using HMAC-SHA256.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

    Returns parsed user dict if valid.
    Raises ValueError if invalid.
    """
    parsed = urllib.parse.parse_qs(init_data)

    # Extract and remove hash from the data
    received_hash = parsed.pop("hash", [None])[0]
    if not received_hash:
        raise ValueError("Missing hash in initData")

    # Step 1: Build data-check-string (sorted key=value pairs, \n separated)
    data_check_pairs = []
    for key in sorted(parsed.keys()):
        val = parsed[key][0]
        data_check_pairs.append(f"{key}={val}")
    data_check_string = "\n".join(data_check_pairs)

    # Step 2: Create secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()

    # Step 3: Calculate HMAC-SHA256(secret_key, data_check_string)
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # Step 4: Compare
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid initData signature")

    # Parse user JSON
    user_json = parsed.get("user", [None])[0]
    if not user_json:
        raise ValueError("No user data in initData")

    return json.loads(user_json)


# ──────────────────────────────────────────────
# Authentication Dependency
# ──────────────────────────────────────────────

async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    x_dev_user_id: Optional[int] = Header(None),
    db: AsyncSession = Depends(get_session),
) -> User:
    """
    Authenticates the user from Telegram WebApp initData.

    In development mode (APP_ENV=development), allows X-Dev-User-Id header
    for Swagger/local testing.
    """

    telegram_id: Optional[int] = None

    # --- 1. Try Telegram initData (production path) ---
    if x_telegram_init_data:
        try:
            user_obj = _validate_telegram_init_data(
                x_telegram_init_data, settings.BOT_TOKEN
            )
            telegram_id = user_obj.get("id")
        except ValueError as e:
            logger.warning(f"Invalid Telegram initData: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid Telegram authorization: {e}")

    # --- 2. Dev fallback (only in development mode) ---
    if not telegram_id and settings.APP_ENV == "development" and x_dev_user_id:
        logger.warning(f"DEV MODE: Using X-Dev-User-Id={x_dev_user_id}")
        telegram_id = x_dev_user_id

    # --- 3. No auth at all → reject ---
    if not telegram_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide X-Telegram-Init-Data header.",
        )

    # --- 4. DB Lookup ---
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Auto-create user & link to first restaurant
        stmt_rest = select(Restaurant).limit(1)
        res_rest = await db.execute(stmt_rest)
        restaurant = res_rest.scalar_one_or_none()

        if not restaurant:
            restaurant = Restaurant(
                id=uuid.uuid4(),
                iiko_id=uuid.uuid4(),
                name="Default Restaurant",
                time_zone="Europe/Moscow",
            )
            db.add(restaurant)
            await db.flush()

        user = User(
            telegram_id=telegram_id,
            linked_restaurant_id=restaurant.id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


# ──────────────────────────────────────────────
# RBAC Helpers
# ──────────────────────────────────────────────

def require_role(user: User, *allowed_roles: UserRole) -> None:
    """
    Raises 403 if user's role is not in the allowed list.
    """
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}. "
                   f"Your role: {user.role.value}",
        )
