# Standard library imports
from typing import Dict, Any, Optional

# Third-party library imports
from fastapi import APIRouter, Depends, HTTPException

# Local application imports
from handlers.payment_handler import PaymentHandler
from handlers.auth_handlers import AuthHandler
from models.user_model import User as UserModel
from dto.payment_dto import (
    PaymentLinkRequest,
    PaymentLinkResponse,
    PaymentVerificationRequest,
    PaymentWebhookRequest,
    PaymentStatusResponse
)
from dependencies.logger import logger
from models.payment_model import Order
from models.payment_model import Payment
import uuid

# Create router
payment_router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@payment_router.post("/create", response_model=PaymentLinkResponse)
async def create_payment_link(
    request: PaymentLinkRequest,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
):
    """
    Create a payment link for purchasing credits.
    """
    return await PaymentHandler.create_payment_link(request, current_user)


@payment_router.get("/verify")
async def verify_payment(
    razorpay_payment_id: str,
    razorpay_payment_link_id: str,
    razorpay_signature: str,
    razorpay_payment_link_reference_id: Optional[str] = None,
    razorpay_payment_link_status: Optional[str] = None
):
    """
    Verify a payment from Razorpay callback.
    """
    logger.info("====================== PAYMENT VERIFICATION STARTED ======================")
    logger.info(f"CALLBACK RECEIVED: payment_id={razorpay_payment_id}, link_id={razorpay_payment_link_id}")
    logger.info(f"Payment status from Razorpay: {razorpay_payment_link_status}")

    request = PaymentVerificationRequest(
        razorpay_payment_id=razorpay_payment_id,
        razorpay_payment_link_id=razorpay_payment_link_id,
        razorpay_signature=razorpay_signature,
        razorpay_payment_link_reference_id=razorpay_payment_link_reference_id,
        razorpay_payment_link_status=razorpay_payment_link_status
    )

    result = await PaymentHandler.verify_payment(request)
    logger.info(f"VERIFICATION RESULT: {result}")
    logger.info("====================== PAYMENT VERIFICATION COMPLETED ======================")
    return result


@payment_router.post("/manual-verify")
async def manual_verify_payment(
    payment_link_id: str,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
):
    """
    Manually verify a payment for testing purposes.
    """
    logger.info(f"Manual verification for payment link ID: {payment_link_id}")

    # Find the order
    order = Order.objects(razorpay_payment_link_id=payment_link_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update order status
    order.status = "paid"
    order.save()

    # Create a dummy payment ID
    payment_id = f"manual_pay_{uuid.uuid4().hex[:10]}"

    # Create payment record
    payment = Payment(
        order=order,
        payment_id=payment_id,
        user=order.user,
        amount=order.amount,
        currency=order.currency,
        payment_method="manual",
        status="captured",
        signature="manual_verification"
    )
    payment.save()

    # Add credits to user
    user = order.user
    user.credits += order.credits_purchased
    user.save()

    return {
        "success": True,
        "message": "Payment manually verified",
        "order_id": order.order_id,
        "payment_id": payment_id,
        "amount": order.amount,
        "credits_purchased": order.credits_purchased
    }


@payment_router.post("/webhook", response_model=Dict[str, Any])
async def handle_webhook(request: PaymentWebhookRequest):
    """
    Handle webhook events from Razorpay.
    """
    return await PaymentHandler.handle_webhook(request)


@payment_router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: str,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
):
    """
    Get the status of a payment.
    """
    return await PaymentHandler.get_payment_status(order_id, current_user)
