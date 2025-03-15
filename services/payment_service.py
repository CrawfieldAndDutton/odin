# Standard library imports
from typing import Dict, Any

# Third-party library imports
from pytz import timezone

# Local application imports
from services.base_services import BaseService
from dependencies.constants import RAZORPAY_PAYMENT_LINK_PAYLOAD
from dependencies.razorpay_templates import RAZORPAY_DYNAMIC_VALUES_TEMPLATE
from models.user_model import User

# Define IST timezone
ist = timezone('Asia/Kolkata')


class PaymentService:
    """
    Service for handling payment-related operations with Razorpay.
    """

    @staticmethod
    async def create_payment_link(
        user: User,
        amount: float,
        credits_purchased: int
    ) -> Dict[str, Any]:
        """
        Create a payment link using Razorpay.

        Args:
            user: User requesting the payment link
            amount: Amount to be paid (in INR)
            credits_purchased: Number of credits to be purchased

        Returns:
            Dict: Razorpay payment link response
        """

        client = BaseService.get_razorpay_client()

        # Generate a unique reference ID

        # Create dynamic values using the template
        dynamic_values = RAZORPAY_DYNAMIC_VALUES_TEMPLATE.copy()

        # Set values in the template
        dynamic_values["amount"] = int(amount * 100)  # Convert to paise
        dynamic_values["description"] = f"Purchase of {credits_purchased} credits"
        dynamic_values["customer"]["name"] = f"{user.first_name} {user.last_name}".strip()
        dynamic_values["customer"]["email"] = user.email
        dynamic_values["customer"]["contact"] = user.phone_number
        dynamic_values["notes"]["user_id"] = str(user.id)
        dynamic_values["notes"]["credits_purchased"] = str(credits_purchased)

        # Merge the constant payload with dynamic values
        payment_link_data = {**RAZORPAY_PAYMENT_LINK_PAYLOAD, **dynamic_values}

        # Create payment link
        return client.payment_link.create(payment_link_data)
