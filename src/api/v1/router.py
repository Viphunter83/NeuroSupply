from fastapi import APIRouter
from src.api.v1.endpoints import orders

api_router = APIRouter()
api_router.include_router(orders.router, prefix="/order", tags=["orders"])
