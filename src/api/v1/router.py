from fastapi import APIRouter
from src.api.endpoints import order

api_router = APIRouter()
api_router.include_router(order.router, prefix="/order", tags=["order"])
