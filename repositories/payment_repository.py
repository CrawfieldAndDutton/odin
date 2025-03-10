# Standard library imports
from typing import Optional, List, Dict, Any
import uuid

# Third-party library imports
from mongoengine.errors import DoesNotExist
# from fastapi import HTTPException, Depends

# Local application imports
from dependencies.logger import logger
from models.payment_model import Order, Payment
from models.user_model import User
from services.payment_service import PaymentService
# from handlers.auth_handlers import AuthHandler
# from dto.payment_dto import (
#     PaymentLinkRequest,
#     PaymentLinkResponse,
#     PaymentVerificationRequest,
#     PaymentVerificationResponse,
#     PaymentWebhookRequest,
#     PaymentStatusResponse
# )


class PaymentRepository:
    """Repository for payment-related database operations."""

    @staticmethod
    def get_order_by_id(order_id: str) -> Optional[Order]:
        """
        Get an order by its ID.

        Args:
            order_id: The order ID to search for

        Returns:
            Order or None: The order if found, None otherwise
        """
        try:
            return Order.objects.get(order_id=order_id)
        except DoesNotExist:
            logger.error(f"Order not found with ID: {order_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving order: {str(e)}")
            return None

    @staticmethod
    def get_order_by_payment_link_id(payment_link_id: str) -> Optional[Order]:
        """
        Get an order by its Razorpay payment link ID.

        Args:
            payment_link_id: The Razorpay payment link ID to search for

        Returns:
            Order or None: The order if found, None otherwise
        """
        try:
            return Order.objects.get(razorpay_payment_link_id=payment_link_id)
        except DoesNotExist:
            logger.error(f"Order not found with payment link ID: {payment_link_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving order by payment link ID: {str(e)}")
            return None

    @staticmethod
    def get_payment_by_id(payment_id: str) -> Optional[Payment]:
        """
        Get a payment by its ID.

        Args:
            payment_id: The payment ID to search for

        Returns:
            Payment or None: The payment if found, None otherwise
        """
        try:
            return Payment.objects.get(payment_id=payment_id)
        except DoesNotExist:
            logger.error(f"Payment not found with ID: {payment_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving payment: {str(e)}")
            return None

    @staticmethod
    def get_user_orders(user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """
        Get orders for a specific user.

        Args:
            user_id: The user ID to get orders for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List[Order]: List of orders for the user
        """
        try:
            user = User.objects.get(id=user_id)
            return Order.objects(user=user).order_by('-created_at').skip(skip).limit(limit)
        except DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving user orders: {str(e)}")
            return []

    @staticmethod
    def get_user_payments(user_id: str, skip: int = 0, limit: int = 10) -> List[Payment]:
        """
        Get payments for a specific user.

        Args:
            user_id: The user ID to get payments for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List[Payment]: List of payments for the user
        """
        try:
            user = User.objects.get(id=user_id)
            return Payment.objects(user=user).order_by('-created_at').skip(skip).limit(limit)
        except DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving user payments: {str(e)}")
            return []

    @staticmethod
    def update_order_status(order_id: str, status: str) -> bool:
        """
        Update the status of an order.

        Args:
            order_id: Order ID to update
            status: New status value

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            order = Order.objects.get(order_id=order_id)
            order.status = status
            order.save()
            return True
        except DoesNotExist:
            logger.error(f"Order not found with ID: {order_id}")
            return False
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return False

    @staticmethod
    async def verify_payment(
        razorpay_payment_id: str,
        razorpay_payment_link_id: str,
        razorpay_signature: str
    ) -> Dict[str, Any]:
        """
        Verify payment signature from Razorpay.
        """
        try:
            logger.info("====================== PAYMENT REPOSITORY STARTED ======================")
            logger.info(
                f"Repository verifying payment: payment_id={razorpay_payment_id}, link_id={razorpay_payment_link_id}")

            # Get Razorpay client
            try:
                client = PaymentService.get_razorpay_client()
                logger.info("Razorpay client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Razorpay client: {str(e)}")
                return {
                    "success": False,
                    "message": f"Failed to initialize Razorpay client: {str(e)}"
                }

            # Find the order in our database using payment_link_id
            try:
                order = Order.objects(razorpay_payment_link_id=razorpay_payment_link_id).first()
                if order:
                    logger.info(f"Found order: {order.order_id} with status {order.status}")
                    logger.info(
                        f"Order details: amount={order.amount}, credits={order.credits_purchased}, "
                        f"user={order.user.id}")
                else:
                    logger.error(f"Order not found for payment link ID: {razorpay_payment_link_id}")
                    return {
                        "success": False,
                        "message": "Order not found"
                    }
            except Exception as e:
                logger.error(f"Error finding order: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error finding order: {str(e)}"
                }

            # Prepare data for verification
            params_dict = {
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_payment_link_id': razorpay_payment_link_id,
                'razorpay_signature': razorpay_signature
            }
            logger.info(f"Verification params: {params_dict}")

            # Verify signature
            try:
                client.utility.verify_payment_signature(params_dict)
                logger.info("Signature verification successful")
            except Exception as e:
                logger.error(f"Signature verification failed: {str(e)}")
                return {
                    "success": False,
                    "message": f"Signature verification failed: {str(e)}"
                }

            # Get payment details from Razorpay
            try:
                payment_details = client.payment.fetch(razorpay_payment_id)
                logger.info(f"Payment details from Razorpay: {payment_details}")
            except Exception as e:
                logger.error(f"Failed to fetch payment details: {str(e)}")
                logger.info("Using default payment details")
                payment_details = {"status": "captured", "method": "unknown"}

            # Update order status
            try:
                logger.info(f"Updating order status from {order.status} to paid")
                order.status = "paid"
                order.save()
                logger.info("Order status updated successfully")
            except Exception as e:
                logger.error(f"Failed to update order status: {str(e)}")
                return {
                    "success": False,
                    "message": f"Failed to update order status: {str(e)}"
                }

            # Check if payment already exists to avoid duplicates
            try:
                existing_payment = Payment.objects(payment_id=razorpay_payment_id).first()
                if existing_payment:
                    logger.info(f"Payment already exists: {razorpay_payment_id}")

                    # Still update user credits if needed
                    user = order.user
                    logger.info(f"User current credits: {user.credits}")
                    if order.status == "paid":
                        logger.info(f"Adding {order.credits_purchased} credits to user {user.id}")
                        user.credits += order.credits_purchased
                        user.save()
                        logger.info(f"User credits updated to: {user.credits}")

                    return {
                        "success": True,
                        "message": "Payment already processed",
                        "order_id": order.order_id,
                        "payment_id": razorpay_payment_id,
                        "amount": order.amount,
                        "credits_purchased": order.credits_purchased
                    }
            except Exception as e:
                logger.error(f"Error checking existing payment: {str(e)}")

            # Create payment record
            try:
                logger.info("Creating payment record")
                payment = Payment(
                    order=order,
                    payment_id=razorpay_payment_id,
                    user=order.user,
                    amount=order.amount,
                    currency=order.currency,
                    payment_method=payment_details.get("method", ""),
                    status="captured",  # For payment links, we can assume it's captured if we get the callback
                    signature=razorpay_signature
                )
                payment.save()
                logger.info(f"Payment record created successfully: {payment.id}")
            except Exception as e:
                logger.error(f"Failed to create payment record: {str(e)}")
                return {
                    "success": False,
                    "message": f"Failed to create payment record: {str(e)}"
                }

            # Add credits to user
            try:
                user = order.user
                logger.info(f"User current credits: {user.credits}")
                logger.info(f"Adding {order.credits_purchased} credits to user {user.id}")
                user.credits += order.credits_purchased
                user.save()
                logger.info(f"User credits updated to: {user.credits}")
            except Exception as e:
                logger.error(f"Failed to update user credits: {str(e)}")
                return {
                    "success": False,
                    "message": f"Failed to update user credits: {str(e)}"
                }

            logger.info("Payment verification completed successfully")
            logger.info("====================== PAYMENT REPOSITORY COMPLETED ======================")
            return {
                "success": True,
                "message": "Payment verified successfully",
                "order_id": order.order_id,
                "payment_id": razorpay_payment_id,
                "amount": order.amount,
                "credits_purchased": order.credits_purchased
            }

        except Exception as e:
            logger.error("====================== PAYMENT REPOSITORY ERROR ======================")
            logger.error(f"Payment verification error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": f"Payment verification failed: {str(e)}"
            }

    @staticmethod
    async def manual_verify_payment(payment_link_id: str) -> Dict[str, Any]:
        """
        Manually verify a payment for testing purposes.

        Args:
            payment_link_id: Payment Link ID to verify

        Returns:
            Dict: Verification result
        """
        try:
            logger.info(f"Manual verification for payment link ID: {payment_link_id}")

            # Find the order
            order = Order.objects(razorpay_payment_link_id=payment_link_id).first()

            if not order:
                logger.error(f"Order not found for payment link ID: {payment_link_id}")
                return {
                    "success": False,
                    "message": "Order not found"
                }

            # Update order status
            order.status = "paid"
            order.save()
            logger.info("Updated order status to paid")

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
            logger.info(f"Created payment record: {payment_id}")

            # Add credits to user
            user = order.user
            logger.info(f"User current credits: {user.credits}")
            user.credits += order.credits_purchased
            user.save()
            logger.info(f"Added {order.credits_purchased} credits to user {user.id}")

            return {
                "success": True,
                "message": "Payment manually verified",
                "order_id": order.order_id,
                "payment_id": payment_id,
                "amount": order.amount,
                "credits_purchased": order.credits_purchased
            }

        except Exception as e:
            logger.error(f"Manual verification error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": f"Manual verification failed: {str(e)}"
            }
