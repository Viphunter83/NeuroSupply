from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps import get_current_user, get_session, require_role
from src.db.models.user import User, UserRole
from src.db.models.restaurant import Restaurant
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
from src.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    linked_restaurant_id: Optional[uuid.UUID] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.COOK


@router.post("/signup", response_model=Token)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_session)):
    """Register a new user."""
    # Check if user exists
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new restaurant if none linked? For now, we need to link to one
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
        id=uuid.uuid4(),
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        linked_restaurant_id=restaurant.id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_session)):
    """Login with email and password."""
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    """Return current user info and their linked restaurant."""
    stmt = select(Restaurant).where(Restaurant.id == current_user.linked_restaurant_id)
    result = await db.execute(stmt)
    restaurant = result.scalar_one_or_none()
    
    return {
        "id": str(current_user.id),
        "telegram_id": current_user.telegram_id,
        "supabase_user_id": str(current_user.supabase_user_id) if current_user.supabase_user_id else None,
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
            "id": str(u.id),
            "email": u.email,
            "telegram_id": u.telegram_id,
            "role": u.role.value,
            "restaurant_id": str(u.linked_restaurant_id) if u.linked_restaurant_id else None,
            "restaurant_name": rest_name
        })
    return res

@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Update user role or restaurant (Manager/Admin only)."""
    require_role(current_user, UserRole.MANAGER, UserRole.ADMIN)
    
    stmt = select(User).where(User.id == user_id)
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
