from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Restaurant
from src.schemas.restaurant import RestaurantResponse, RestaurantSettingsUpdate, RestaurantSettings
from src.api.v1.endpoints.auth import get_current_user
from src.db.models.user import User, UserRole
from src.services.iiko.sync_service import IikoSyncService

router = APIRouter()

@router.get("/", response_model=List[RestaurantResponse])
async def list_restaurants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all restaurants (Admin/Manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    stmt = select(Restaurant)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific restaurant settings"""
    # Authorization check
    if current_user.role != UserRole.ADMIN:
        if current_user.linked_restaurant_id != restaurant_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await db.execute(stmt)
    restaurant = result.scalar_one_or_none()
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
        
    return restaurant

@router.patch("/{restaurant_id}/settings", response_model=RestaurantResponse)
async def update_restaurant_settings(
    restaurant_id: UUID,
    update_data: RestaurantSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update restaurant settings (Admin/Manager only)"""
    # Authorization check
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if current_user.role == UserRole.MANAGER and current_user.linked_restaurant_id != restaurant_id:
        raise HTTPException(status_code=403, detail="Cannot manage other restaurants")

    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await db.execute(stmt)
    restaurant = result.scalar_one_or_none()
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Update settings JSON
    restaurant.settings = update_data.settings.model_dump()
    
    await db.commit()
    await db.refresh(restaurant)
    return restaurant

@router.post("/{restaurant_id}/sync")
async def sync_restaurant_data(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger direct sync from iiko for this restaurant"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    sync_service = IikoSyncService(db)
    try:
        await sync_service.sync_stock_balances(restaurant_id)
        await sync_service.sync_recipes(restaurant_id)
        return {"status": "success", "message": "Synced stock and recipes from iiko"}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
