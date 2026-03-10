from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps import get_current_user, get_session, require_role
from src.db.models.user import User, UserRole
from src.db.models.restaurant import Restaurant
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import uuid

router = APIRouter()

class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    linked_restaurant_id: Optional[uuid.UUID] = None

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    """Return current user info and their linked restaurant."""
    stmt = select(Restaurant).where(Restaurant.id == current_user.linked_restaurant_id)
    result = await db.execute(stmt)
    restaurant = result.scalar_one_or_none()
    
    return {
        "id": str(current_user.telegram_id), # Use telegram_id as ID
        "telegram_id": current_user.telegram_id,
        "role": current_user.role.value,
        "restaurant": {
            "id": str(restaurant.id) if restaurant else None,
            "name": restaurant.name if restaurant else "No Restaurant Linked"
        } if restaurant else None
    }

@router.post("/join/{restaurant_id}")
async def join_restaurant(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Link current user to a specific restaurant."""
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await db.execute(stmt)
    restaurant = result.scalar_one_or_none()
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    current_user.linked_restaurant_id = restaurant_id
    await db.commit()
    
    return {"status": "success", "restaurant_name": restaurant.name}

@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """List all users (Manager/Admin only)."""
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    
    stmt = select(User).order_by(User.telegram_id)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    # Enrich with restaurant names
    res = []
    for u in users:
        rest_name = "None"
        if u.linked_restaurant_id:
            rest_stmt = select(Restaurant).where(Restaurant.id == u.linked_restaurant_id)
            rest = (await db.execute(rest_stmt)).scalar_one_or_none()
            if rest:
                rest_name = rest.name
        
        res.append({
            "id": str(u.telegram_id),
            "telegram_id": u.telegram_id,
            "role": u.role.value,
            "restaurant_id": str(u.linked_restaurant_id) if u.linked_restaurant_id else None,
            "restaurant_name": rest_name
        })
    return res

@router.patch("/users/{user_id}")
async def update_user(
    user_id: int, # telegram_id is int
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Update user role or restaurant (Manager/Admin only)."""
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    
    stmt = select(User).where(User.telegram_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if data.role is not None:
        user.role = data.role
    if data.linked_restaurant_id is not None:
        user.linked_restaurant_id = data.linked_restaurant_id
        
    await db.commit()
    return {"status": "success"}
