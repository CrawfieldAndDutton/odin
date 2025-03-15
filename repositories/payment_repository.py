# Standard library imports
from typing import Optional

# Third-party library imports
from mongoengine.errors import DoesNotExist

# Local application imports
from dependencies.logger import logger
from models.payment_model import PaymentTransaction
from pytz import timezone


# Define IST timezone
ist = timezone('Asia/Kolkata')


class PaymentRepository:
    """Repository for payment-related database operations."""

    @staticmethod
    def get_transaction_by_order_id(order_id: str) -> Optional[PaymentTransaction]:
        """
        Get a payment transaction by its order ID.

        Args:
            order_id: The order ID to search for

        Returns:
            PaymentTransaction or None: The transaction if found, None otherwise
        """
        try:
            return PaymentTransaction.objects.get(order_id=order_id)
        except DoesNotExist:
            logger.error(f"Payment transaction not found with order ID: {order_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving payment transaction: {str(e)}")
            return None

    @staticmethod
    def get_transaction_by_payment_link_id(payment_link_id: str) -> Optional[PaymentTransaction]:
        """
        Get a payment transaction by its Razorpay payment link ID.

        Args:
            payment_link_id: The Razorpay payment link ID to search for

        Returns:
            PaymentTransaction or None: The transaction if found, None otherwise
        """
        try:
            return PaymentTransaction.objects.get(razorpay_payment_link_id=payment_link_id)
        except DoesNotExist:
            logger.error(f"Payment transaction not found with payment link ID: {payment_link_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving payment transaction by payment link ID: {str(e)}")
            return None

    @staticmethod
    def get_transaction_by_payment_id(payment_id: str) -> Optional[PaymentTransaction]:
        """
        Get a payment transaction by its payment ID.

        Args:
            payment_id: The payment ID to search for

        Returns:
            PaymentTransaction or None: The transaction if found, None otherwise
        """
        try:
            return PaymentTransaction.objects.get(payment_id=payment_id)
        except DoesNotExist:
            logger.error(f"Payment transaction not found with payment ID: {payment_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving payment transaction: {str(e)}")
            return None

    @staticmethod
    def update_transaction_status(order_id: str, order_status: str, payment_status: str = None) -> bool:
        """
        Update the status of a payment transaction.

        Args:
            order_id: Order ID to update
            order_status: New order status value
            payment_status: New payment status value (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            transaction = PaymentTransaction.objects.get(order_id=order_id)
            transaction.order_status = order_status
            if payment_status:
                transaction.payment_status = payment_status
            transaction.save()
            return True
        except DoesNotExist:
            logger.error(f"Payment transaction not found with order ID: {order_id}")
            return False
        except Exception as e:
            logger.error(f"Error updating payment transaction status: {str(e)}")
            return False
