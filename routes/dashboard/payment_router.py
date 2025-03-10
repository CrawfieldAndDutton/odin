# Standard library imports
from typing import List, Dict, Any

# Third-party library imports
from fastapi import APIRouter, Depends, Query

# Local application imports
from handlers.payment_handler import PaymentHandler
from handlers.auth_handlers import AuthHandler
from models.user_model import User as UserModel
from repositories.payment_repository import PaymentRepository
from dto.payment_dto import PaymentStatusResponse

# Create router
dashboard_payment_router = APIRouter(prefix="/dashboard/api/v1/payments", tags=["dashboard-payments"])


@dashboard_payment_router.get("/orders", response_model=List[Dict[str, Any]])
async def get_user_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
):
    """
    Get orders for the current user.
    """
    orders = PaymentRepository.get_user_orders(str(current_user.id), skip, limit)

    result = []
    for order in orders:
        result.append({
            "order_id": order.order_id,
            "amount": order.amount,
            "currency": order.currency,
            "status": order.status,
            "credits_purchased": order.credits_purchased,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        })

    return result


@dashboard_payment_router.get("/payments", response_model=List[Dict[str, Any]])
async def get_user_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
):
    """
    Get payments for the current user.
    """
    payments = PaymentRepository.get_user_payments(str(current_user.id), skip, limit)

    result = []
    for payment in payments:
        result.append({
            "payment_id": payment.payment_id,
            "order_id": payment.order.order_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "status": payment.status,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at
        })

    return result


@dashboard_payment_router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: str,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
):
    """
    Get the status of a payment.
    """
    return await PaymentHandler.get_payment_status(order_id, current_user)
