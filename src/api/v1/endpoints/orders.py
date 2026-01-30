from fastapi import APIRouter, Depends
from uuid import UUID
from src.services.order import OrderService
from src.services.calculation import CalculationService
from src.schemas.order import OrderDraftResponse, OrderVerifyRequest

router = APIRouter()

@router.get("/draft", response_model=OrderDraftResponse)
async def get_order_draft(
    restaurant_id: UUID,
    calc_service: CalculationService = Depends()
):
    return await calc_service.calculate_draft(restaurant_id)

@router.post("/verify")
async def verify_order(
    request: OrderVerifyRequest,
    order_service: OrderService = Depends()
):
    return await order_service.create_order(request)
