from fastapi import APIRouter

from src.api.v1.endpoints import (
    orders, analytics, products, anomalies, auth, sales_plans, restaurants
)

api_router = APIRouter()
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sales_plans.router, prefix="/sales-plans", tags=["sales-plans"])
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["restaurants"])
