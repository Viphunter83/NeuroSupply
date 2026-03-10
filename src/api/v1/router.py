from fastapi import APIRouter
from src.api.v1.endpoints import orders
from src.api.v1.endpoints import analytics
from src.api.v1.endpoints import products
from src.api.v1.endpoints import anomalies
from src.api.v1.endpoints import auth

api_router = APIRouter()
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
