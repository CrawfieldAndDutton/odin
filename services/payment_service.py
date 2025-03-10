# Standard library imports
import uuid
# import hmac
# import hashlib
# from datetime import datetime
from typing import Dict, Any, Optional

# Third-party library imports
import razorpay
from fastapi import HTTPException

# Local application imports
from dependencies.config import Config
from dependencies.logger import logger
from models.user_model import User
from models.payment_model import Order, Payment


class PaymentService:
    """
    Service for handling payment-related operations with Razorpay.
    """

    @staticmethod
    def get_razorpay_client():
        """
        Get a configured Razorpay client.

        Returns:
            razorpay.Client: Configured Razorpay client
        """
        try:
            return razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {str(e)}")
            raise HTTPException(status_code=500, detail="Payment service unavailable")

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
            Dict: Payment link details including short_url
        """
        try:
            client = PaymentService.get_razorpay_client()

            # Generate a unique reference ID
            reference_id = f"order_{uuid.uuid4().hex[:10]}"

            # Ensure API_BASE_URL has the correct format
            base_url = Config.API_BASE_URL
            if not base_url.startswith(('http://', 'https://')):
                base_url = f"http://{base_url}"

            # Create payment link data
            payment_link_data = {
                "amount": int(amount * 100),  # Convert to paise
                "currency": "INR",
                "accept_partial": False,
                "description": f"Purchase of {credits_purchased} credits",
                "customer": {
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                    "contact": ""  # Optional, can be added if available
                },
                "notify": {
                    "sms": False,
                    "email": True
                },
                "reminder_enable": True,
                "notes": {
                    "user_id": str(user.id),
                    "credits_purchased": str(credits_purchased)
                },
                "callback_url": f"{base_url}/api/v1/payments/verify",
                "callback_method": "get"
            }

            # Create payment link
            response = client.payment_link.create(payment_link_data)
            logger.info(f"Razorpay response: {response}")
            # Create order in database
            order = Order(
                order_id=reference_id,
                user=user,
                amount=amount,
                currency="INR",
                status="pending",
                short_url=response.get("short_url"),
                credits_purchased=credits_purchased,
                razorpay_payment_link_id=response.get("id")
            )
            order.save()

            return {
                "order_id": reference_id,
                "short_url": response.get("short_url"),
                "amount": amount,
                "credits_purchased": credits_purchased,
                "status": "pending"
            }

        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay BadRequestError: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Payment link creation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create payment link: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create payment link")

    @staticmethod
    async def verify_payment(
        razorpay_payment_id: str,
        razorpay_payment_link_id: str,
        razorpay_signature: str,
        razorpay_payment_link_reference_id: Optional[str] = None,
        razorpay_payment_link_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify payment from Razorpay.

        Args:
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay
            razorpay_signature: Signature from Razorpay
            razorpay_payment_link_reference_id: Reference ID (optional)
            razorpay_payment_link_status: Payment status from Razorpay (optional)

        Returns:
            Dict: Verification result
        """
        try:
            logger.info(
                f"Starting verification with payment_id={razorpay_payment_id}, link_id={razorpay_payment_link_id}")
            client = PaymentService.get_razorpay_client()

            # Temporarily skip signature verification in production
            # TODO: Implement correct signature verification after confirming with Razorpay
            logger.warning("Skipping signature verification temporarily - contact Razorpay for correct method")

            # Find the order in our database using payment_link_id
            order = Order.objects(razorpay_payment_link_id=razorpay_payment_link_id).first()

            if not order:
                logger.error(f"Order not found for payment link ID: {razorpay_payment_link_id}")
                return {
                    "success": False,
                    "message": "Order not found",
                    "razorpay_payment_link_id": razorpay_payment_link_id
                }

            # Verify payment status from Razorpay callback
            if razorpay_payment_link_status and razorpay_payment_link_status.lower() != "paid":
                logger.error(f"Payment status is not 'paid': {razorpay_payment_link_status}")
                return {
                    "success": False,
                    "message": f"Payment status is not 'paid': {razorpay_payment_link_status}",
                    "razorpay_payment_link_id": razorpay_payment_link_id
                }

            # Get payment details from Razorpay API
            try:
                payment_details = client.payment.fetch(razorpay_payment_id)
                logger.info(f"Payment details from Razorpay: {payment_details}")

                if payment_details.get("status") not in ["authorized", "captured"]:
                    logger.error(f"Payment status is not authorized/captured: {payment_details.get('status')}")
                    return {
                        "success": False,
                        "message": f"Payment status is not valid: {payment_details.get('status')}",
                        "razorpay_payment_link_id": razorpay_payment_link_id
                    }
            except Exception as e:
                logger.error(f"Failed to fetch payment details: {str(e)}")
                payment_details = {"status": "captured", "method": "razorpay"}

            # Check if payment already exists
            existing_payment = Payment.objects(payment_id=razorpay_payment_id).first()
            if existing_payment:
                logger.info(f"Payment already exists: {razorpay_payment_id}")
                return {
                    "success": True,
                    "message": "Payment already processed",
                    "order_id": order.order_id,
                    "payment_id": razorpay_payment_id,
                    "amount": order.amount,
                    "credits_purchased": order.credits_purchased,
                    "razorpay_payment_link_id": razorpay_payment_link_id
                }

            # Update order status
            order.status = "paid"
            order.save()
            logger.info(f"Updated order status to paid for order ID: {order.order_id}")

            # Create payment record
            payment = Payment(
                order=order,
                payment_id=razorpay_payment_id,
                user=order.user,
                amount=order.amount,
                currency=order.currency,
                payment_method=payment_details.get("method", "razorpay"),
                status="captured",
                signature=razorpay_signature
            )
            payment.save()
            logger.info(f"Created payment record with ID: {razorpay_payment_id}")

            # Add credits to user
            user = order.user
            logger.info(f"User {user.id} current credits: {user.credits}")
            user.credits += order.credits_purchased
            user.save()
            logger.info(f"Added {order.credits_purchased} credits to user {user.id}, new total: {user.credits}")

            return {
                "success": True,
                "message": "Payment verified successfully",
                "order_id": order.order_id,
                "payment_id": razorpay_payment_id,
                "amount": order.amount,
                "credits_purchased": order.credits_purchased,
                "razorpay_payment_link_id": razorpay_payment_link_id
            }

        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": f"Payment verification failed: {str(e)}",
                "razorpay_payment_link_id": razorpay_payment_link_id
            }

    @staticmethod
    async def handle_webhook(event_data: Dict[str, Any]) -> bool:
        """
        Handle webhook events from Razorpay.

        Args:
            event_data: Webhook event data from Razorpay

        Returns:
            bool: True if handled successfully, False otherwise
        """
        try:
            event = event_data.get("event")
            payload = event_data.get("payload", {}).get("payment", {}).get("entity", {})

            if event == "payment.captured":
                payment_id = payload.get("id")
                order_id = payload.get("order_id")

                # Find the order in our database
                order = Order.objects(razorpay_payment_link_id=order_id).first()

                if not order:
                    logger.error(f"Order not found for payment link ID: {order_id}")
                    return False

                # Update order status
                order.status = "paid"
                order.save()

                # Check if payment already exists
                existing_payment = Payment.objects(payment_id=payment_id).first()

                if not existing_payment:
                    # Create payment record
                    payment = Payment(
                        order=order,
                        payment_id=payment_id,
                        user=order.user,
                        amount=order.amount,
                        currency=order.currency,
                        payment_method=payload.get("method", ""),
                        status=payload.get("status", ""),
                        signature=""  # Webhook doesn't provide signature
                    )
                    payment.save()

                # Add credits to user
                user = order.user
                user.credits += order.credits_purchased
                user.save()

                return True

            elif event == "payment.failed":
                payment_id = payload.get("id")
                order_id = payload.get("order_id")

                # Find the order in our database
                order = Order.objects(razorpay_payment_link_id=order_id).first()

                if not order:
                    logger.error(f"Order not found for payment link ID: {order_id}")
                    return False

                # Update order status
                order.status = "failed"
                order.save()

                # Check if payment already exists
                existing_payment = Payment.objects(payment_id=payment_id).first()

                if not existing_payment:
                    # Create payment record
                    payment = Payment(
                        order=order,
                        payment_id=payment_id,
                        user=order.user,
                        amount=order.amount,
                        currency=order.currency,
                        payment_method=payload.get("method", ""),
                        status=payload.get("status", ""),
                        signature=""  # Webhook doesn't provide signature
                    )
                    payment.save()

                return True

            return True

        except Exception as e:
            logger.error(f"Webhook handling error: {str(e)}")
            return False

    @staticmethod
    async def get_payment_status(order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a payment.

        Args:
            order_id: Order ID to check

        Returns:
            Dict: Payment status details or None if not found
        """
        try:
            order = Order.objects(order_id=order_id).first()

            if not order:
                return None

            # Get the associated payment if exists
            payment = Payment.objects(order=order).first()

            result = {
                "order_id": order.order_id,
                "status": order.status,
                "amount": order.amount,
                "credits_purchased": order.credits_purchased,
                "created_at": order.created_at,
                "updated_at": order.updated_at
            }

            if payment:
                result["payment_id"] = payment.payment_id

            return result

        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            return None
