# Standard library imports
from datetime import datetime
from typing import Optional

# Third-party library imports
from pydantic import BaseModel, Field


class PaymentLinkRequest(BaseModel):
    """
    DTO for creating a payment link request.
    """
    amount: float = Field(..., description="Amount to be paid (in INR)")
    credits_purchased: int = Field(..., description="Number of credits to be purchased")


class PaymentLinkResponse(BaseModel):
    """
    DTO for payment link response.
    """
    order_id: str
    short_url: str
    amount: float
    credits_purchased: int
    status: str


class PaymentVerificationRequest(BaseModel):
    """
    DTO for payment verification request.
    """
    razorpay_payment_id: str
    razorpay_payment_link_id: str
    razorpay_signature: str
    razorpay_payment_link_reference_id: Optional[str] = None
    razorpay_payment_link_status: Optional[str] = None


class PaymentVerificationResponse(BaseModel):
    """
    DTO for payment verification response.
    """
    success: bool
    message: str
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    amount: Optional[float] = None
    credits_purchased: Optional[int] = None
    razorpay_payment_link_id: Optional[str] = None


class PaymentWebhookRequest(BaseModel):
    """
    DTO for payment webhook request from Razorpay.
    """
    event: str
    payload: dict
    created_at: int


class PaymentStatusResponse(BaseModel):
    """
    DTO for payment status response.
    """
    order_id: str
    status: str
    amount: float
    credits_purchased: int
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
