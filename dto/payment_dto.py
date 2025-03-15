# Standard library imports
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
