from fastapi import APIRouter
from src.api.v1.endpoints import orders
from src.api.v1.endpoints import analytics

api_router = APIRouter()
api_router.include_router(orders.router, prefix="/order", tags=["orders"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
