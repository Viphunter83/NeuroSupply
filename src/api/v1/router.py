from fastapi import APIRouter
from src.api.v1.endpoints import orders
from src.api.v1.endpoints import analytics
from src.api.v1.endpoints import products

api_router = APIRouter()
api_router.include_router(orders.router, prefix="/order", tags=["orders"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
