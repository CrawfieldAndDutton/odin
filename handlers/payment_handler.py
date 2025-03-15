# Standard library imports
from typing import Dict, Any, Optional, Tuple
import uuid
from datetime import datetime
# Third-party library imports
from fastapi import HTTPException
# import razorpay
# Local application imports
from dependencies.logger import logger
# from handlers.auth_handlers import AuthHandler
from models.user_model import User as UserModel
from services.payment_service import PaymentService
from services.base_services import BaseService
from dto.payment_dto import (
    PaymentLinkRequest,
    PaymentWebhookRequest,
    PaymentVerificationResponse,
)
from models.payment_model import PaymentTransaction
from handlers.user_ledger_transaction_handler import UserLedgerTransactionHandler
from dependencies.configuration import UserLedgerTransactionType
from repositories.payment_repository import PaymentRepository
from pytz import timezone

# Define IST timezone
ist = timezone('Asia/Kolkata')


class PaymentHandler:
    """Handler for payment-related operations."""

    @staticmethod
    async def create_payment_link(
        request: PaymentLinkRequest,
        current_user: UserModel
    ) -> tuple:
        """
        Create a payment link for the user.

        Args:
            request: Payment link request data
            current_user: Current authenticated user

        Returns:
            tuple: (reference_id, razorpay_response)
        """
        logger.info(f"Creating payment link for user {current_user.id} for {request.credits_purchased} credits")

        # Validate request
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero")

        if request.credits_purchased <= 0:
            raise HTTPException(status_code=400, detail="Credits must be greater than zero")

        # Create payment link
        response = await PaymentService.create_payment_link(
            user=current_user,
            amount=request.amount,
            credits_purchased=request.credits_purchased
        )

        # Generate a unique reference ID
        reference_id = f"order_{uuid.uuid4().hex[:10]}"

        # Create payment transaction
        payment_transaction = PaymentTransaction(
            user_id=str(current_user.id),
            total_amount=request.amount,
            currency="INR",
            credits_purchased=request.credits_purchased,
            order_id=reference_id,
            order_status="pending",
            payment_status="pending",
            short_url=response.get("short_url"),
            razorpay_payment_link_id=response.get("id"),
            razorpay_response=response
        )
        payment_transaction.save()

        return reference_id, response

    @staticmethod
    def _validate_payment_params(
        razorpay_payment_id: str,
        razorpay_payment_link_id: str,
        razorpay_signature: str
    ) -> Dict[str, Any]:
        """
        Validate payment verification parameters.

        Args:
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay
            razorpay_signature: Signature from Razorpay

        Returns:
            Dict: Validation result with success flag and message
        """
        if not razorpay_payment_id or not razorpay_payment_link_id or not razorpay_signature:
            logger.error("Missing required payment verification parameters")
            return {
                "success": False,
                "message": "Missing required payment verification parameters"
            }
        return {"success": True}

    @staticmethod
    def _verify_signature(
        client: Any,
        params_dict: Dict[str, str],
        razorpay_payment_link_id: str
    ) -> Dict[str, Any]:
        """
        Verify payment signature from Razorpay.

        Args:
            client: Razorpay client
            params_dict: Parameters for signature verification
            razorpay_payment_link_id: Payment Link ID from Razorpay

        Returns:
            Dict: Verification result with success flag and message
        """
        try:
            logger.info(f"Signature verification params: {params_dict}")
            client.utility.verify_payment_link_signature(params_dict)
            logger.info("Signature verification successful")
            return {"success": True}
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return {
                "success": False,
                "message": f"Signature verification failed: {str(e)}",
                "razorpay_payment_link_id": razorpay_payment_link_id
            }

    @staticmethod
    def _find_payment_transaction(
        razorpay_payment_link_id: str
    ) -> Tuple[bool, Optional[PaymentTransaction], Optional[str]]:
        """
        Find payment transaction by payment link ID.

        Args:
            razorpay_payment_link_id: Payment Link ID from Razorpay

        Returns:
            Tuple: (success, transaction, error_message)
        """
        try:
            # Use repository for database access
            payment_repository = PaymentRepository()
            transaction = payment_repository.get_transaction_by_payment_link_id(razorpay_payment_link_id)

            if not transaction:
                error_msg = f"Payment transaction not found for payment link ID: {razorpay_payment_link_id}"
                logger.error(error_msg)
                return False, None, error_msg

            return True, transaction, None
        except Exception as e:
            error_msg = f"Error finding payment transaction: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    @staticmethod
    def _verify_payment_status(
        razorpay_payment_link_status: Optional[str],
        razorpay_payment_link_id: str
    ) -> Dict[str, Any]:
        """
        Verify payment status from Razorpay callback.

        Args:
            razorpay_payment_link_status: Payment status from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay

        Returns:
            Dict: Verification result with success flag and message
        """
        if not razorpay_payment_link_status:
            return {"success": True}

        logger.info(f"Checking payment status from callback: {razorpay_payment_link_status}")
        if razorpay_payment_link_status.lower() not in ["paid", "authorized", "captured"]:
            error_msg = f"Payment status is not successful: {razorpay_payment_link_status}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "razorpay_payment_link_id": razorpay_payment_link_id
            }
        return {"success": True}

    @staticmethod
    def _get_payment_details(
        client: Any,
        razorpay_payment_id: str
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Get payment details from Razorpay API.

        Args:
            client: Razorpay client
            razorpay_payment_id: Payment ID from Razorpay

        Returns:
            Tuple: (payment_details, error_message)
        """
        try:
            payment_details = client.payment.fetch(razorpay_payment_id)
            logger.info(f"Payment details from Razorpay: {payment_details}")

            # Check payment status from Razorpay API
            payment_status = payment_details.get('status', '').lower()
            logger.info(f"Payment status from Razorpay API: {payment_status}")

            if payment_status not in ["authorized", "captured"]:
                logger.error(f"Payment status is not authorized/captured: {payment_status}")

                # Handle specific failure statuses
                if payment_status in ["failed", "cancelled"]:
                    failure_reason = payment_details.get('error_description', 'Payment was not successful')
                    logger.error(f"Payment failure reason: {failure_reason}")
                    return payment_details, f"Payment {payment_status}: {failure_reason}"

                return payment_details, f"Payment status is not valid: {payment_status}"

            return payment_details, None
        except Exception as e:
            logger.error(f"Failed to fetch payment details: {str(e)}")
            return {"status": "captured", "method": "razorpay"}, None

    @staticmethod
    def _check_already_processed(
        transaction: PaymentTransaction,
        razorpay_payment_id: str,
        razorpay_payment_link_id: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if payment is already processed.

        Args:
            transaction: Payment transaction
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay

        Returns:
            Tuple: (is_already_processed, response_data)
        """
        if (transaction.payment_id == razorpay_payment_id and
                transaction.payment_status in ["captured", "authorized"]):
            logger.info(f"Payment already processed: {razorpay_payment_id}")
            return True, {
                "success": True,
                "message": "Payment already processed",
                "order_id": transaction.order_id,
                "payment_id": razorpay_payment_id,
                "amount": transaction.total_amount,
                "credits_purchased": transaction.credits_purchased,
                "razorpay_payment_link_id": razorpay_payment_link_id
            }
        return False, None

    @staticmethod
    def _update_transaction(
        transaction: PaymentTransaction,
        razorpay_payment_id: str,
        razorpay_signature: str,
        payment_details: Dict[str, Any]
    ) -> bool:
        """
        Update payment transaction with payment details.

        Args:
            transaction: Payment transaction
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            payment_details: Payment details from Razorpay

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            transaction.order_status = "paid"
            transaction.payment_status = "captured"
            transaction.payment_id = razorpay_payment_id
            transaction.payment_method = payment_details.get("method", "razorpay")
            transaction.signature = razorpay_signature
            transaction.payment_response_from_razorpay = payment_details
            transaction.save()

            logger.info(f"Updated payment transaction for order ID: {transaction.order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update payment transaction: {str(e)}")
            return False

    @staticmethod
    def _add_credits_to_user(
        transaction: PaymentTransaction
    ) -> Tuple[bool, Optional[str]]:
        """
        Add credits to user based on payment transaction.

        Args:
            transaction: Payment transaction

        Returns:
            Tuple: (success, error_message)
        """
        try:
            user = UserModel.objects(id=transaction.user_id).first()
            if not user:
                error_msg = f"User not found for ID: {transaction.user_id}"
                logger.error(error_msg)
                return False, error_msg

            logger.info(f"User {user.id} current credits: {user.credits}")

            # Create an instance of UserLedgerTransactionHandler and call increase_credits
            ledger_handler = UserLedgerTransactionHandler()
            ledger_txn = ledger_handler.increase_credits(
                str(user.id),
                float(transaction.credits_purchased),
                UserLedgerTransactionType.CREDIT.value
            )

            if not ledger_txn:
                error_msg = "Failed to create ledger transaction"
                logger.error(error_msg)
                return False, error_msg

            # Refresh user object to get updated credits
            user.reload()

            logger.info(
                f"Added {transaction.credits_purchased} credits to user {user.id}, "
                f"new total: {user.credits}"
            )
            return True, None
        except Exception as e:
            error_msg = f"Failed to update user credits: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def _create_params_dict(
        razorpay_payment_id: str,
        razorpay_payment_link_id: str,
        razorpay_signature: str,
        razorpay_payment_link_reference_id: Optional[str] = None,
        razorpay_payment_link_status: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create parameters dictionary for signature verification.

        Args:
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay
            razorpay_signature: Signature from Razorpay
            razorpay_payment_link_reference_id: Reference ID (optional)
            razorpay_payment_link_status: Payment status from Razorpay (optional)

        Returns:
            Dict: Parameters dictionary for signature verification
        """
        params_dict = {
            'payment_link_id': razorpay_payment_link_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        # Add optional parameters if they exist
        if razorpay_payment_link_reference_id:
            params_dict['payment_link_reference_id'] = razorpay_payment_link_reference_id

        if razorpay_payment_link_status:
            params_dict['payment_link_status'] = razorpay_payment_link_status

        return params_dict

    @staticmethod
    async def verify_payment(
        razorpay_payment_id: str,
        razorpay_payment_link_id: str,
        razorpay_signature: str,
        razorpay_payment_link_reference_id: Optional[str] = None,
        razorpay_payment_link_status: Optional[str] = None
    ) -> PaymentVerificationResponse:
        """
        Verify a payment from Razorpay callback.

        Args:
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay
            razorpay_signature: Signature from Razorpay
            razorpay_payment_link_reference_id: Reference ID (optional)
            razorpay_payment_link_status: Payment status from Razorpay (optional)

        Returns:
            PaymentVerificationResponse: Verification response object
        """
        logger.info("====================== PAYMENT HANDLER STARTED ======================")
        logger.info(f"Handler verifying payment with ID {razorpay_payment_id}")
        logger.info(f"Payment link ID: {razorpay_payment_link_id}")
        logger.info(f"Payment signature: {razorpay_signature}")
        logger.info(f"Payment link reference ID: {razorpay_payment_link_reference_id}")
        logger.info(f"Payment link status: {razorpay_payment_link_status}")

        # Create params dictionary for signature verification
        params_dict = PaymentHandler._create_params_dict(
            razorpay_payment_id,
            razorpay_payment_link_id,
            razorpay_signature,
            razorpay_payment_link_reference_id,
            razorpay_payment_link_status
        )

        # Validate input parameters
        validation_result = PaymentHandler._validate_payment_params(
            razorpay_payment_id,
            razorpay_payment_link_id,
            razorpay_signature
        )
        if not validation_result["success"]:
            logger.warning(f"Payment validation failed: {validation_result.get('message')}")
            return PaymentVerificationResponse(
                success=False,
                message=validation_result.get("message", "Validation failed"),
                order_id=None
            )

        # Get Razorpay client
        client = BaseService.get_razorpay_client()

        # Verify signature
        signature_result = PaymentHandler._verify_signature(
            client, params_dict, razorpay_payment_link_id
        )
        if not signature_result["success"]:
            logger.warning(f"Signature verification failed: {signature_result.get('message')}")
            return PaymentVerificationResponse(
                success=False,
                message=signature_result.get("message", "Signature verification failed"),
                order_id=None,
                razorpay_payment_link_id=razorpay_payment_link_id
            )

        # Find the payment transaction
        success, transaction, error_message = PaymentHandler._find_payment_transaction(
            razorpay_payment_link_id
        )
        if not success:
            logger.warning(f"Transaction not found: {error_message}")
            return PaymentVerificationResponse(
                success=False,
                message=error_message or "Transaction not found",
                order_id=None,
                razorpay_payment_link_id=razorpay_payment_link_id
            )

        # Verify payment status from callback
        status_result = PaymentHandler._verify_payment_status(
            razorpay_payment_link_status, razorpay_payment_link_id
        )
        if not status_result["success"]:
            logger.warning(f"Payment status verification failed: {status_result.get('message')}")
            return PaymentVerificationResponse(
                success=False,
                message=status_result.get("message", "Payment status verification failed"),
                order_id=transaction.order_id,
                razorpay_payment_link_id=razorpay_payment_link_id
            )

        # Process payment details and update transaction
        result = await PaymentHandler._process_payment_details(
            client,
            transaction,
            razorpay_payment_id,
            razorpay_payment_link_id,
            razorpay_signature
        )

        # Create response from result
        if result["success"]:
            logger.info(f"Payment verification successful for order: {result.get('order_id')}")
            response = PaymentVerificationResponse(
                success=True,
                message=result["message"],
                order_id=result.get("order_id"),
                payment_id=result.get("payment_id"),
                amount=result.get("amount"),
                credits_purchased=result.get("credits_purchased"),
                razorpay_payment_link_id=result.get("razorpay_payment_link_id")
            )
        else:
            logger.warning(f"Payment verification failed: {result.get('message')}")
            response = PaymentVerificationResponse(
                success=False,
                message=result["message"],
                order_id=result.get("order_id")
            )

        logger.info(f"Verification result: {response}")
        logger.info("====================== PAYMENT HANDLER COMPLETED ======================")

        return response

    @staticmethod
    async def _process_payment_details(
        client: Any,
        transaction: PaymentTransaction,
        razorpay_payment_id: str,
        razorpay_payment_link_id: str,
        razorpay_signature: str
    ) -> Dict[str, Any]:
        """
        Process payment details and update transaction.

        Args:
            client: Razorpay client
            transaction: Payment transaction
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay
            razorpay_signature: Signature from Razorpay

        Returns:
            Dict: Processing result
        """
        # Get payment details from Razorpay
        payment_details, error_message = PaymentHandler._get_payment_details(
            client, razorpay_payment_id
        )
        if error_message:
            return {
                "success": False,
                "message": error_message,
                "razorpay_payment_link_id": razorpay_payment_link_id
            }

        # Check if payment already processed
        already_processed, response = PaymentHandler._check_already_processed(
            transaction, razorpay_payment_id, razorpay_payment_link_id
        )
        if already_processed:
            return response

        # Update transaction and add credits
        return PaymentHandler._finalize_payment(
            transaction,
            razorpay_payment_id,
            razorpay_signature,
            payment_details,
            razorpay_payment_link_id
        )

    @staticmethod
    def _finalize_payment(
        transaction: PaymentTransaction,
        razorpay_payment_id: str,
        razorpay_signature: str,
        payment_details: Dict[str, Any],
        razorpay_payment_link_id: str
    ) -> Dict[str, Any]:
        """
        Finalize payment by updating transaction and adding credits to user.

        Args:
            transaction: Payment transaction
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            payment_details: Payment details from Razorpay
            razorpay_payment_link_id: Payment Link ID from Razorpay

        Returns:
            Dict: Finalization result
        """
        # Update payment transaction
        update_success = PaymentHandler._update_transaction(
            transaction, razorpay_payment_id, razorpay_signature, payment_details
        )
        if not update_success:
            return {
                "success": False,
                "message": "Failed to update payment transaction",
                "razorpay_payment_link_id": razorpay_payment_link_id
            }

        # Add credits to user
        credits_success, credits_error = PaymentHandler._add_credits_to_user(transaction)
        if not credits_success:
            return {
                "success": False,
                "message": credits_error,
                "razorpay_payment_link_id": razorpay_payment_link_id
            }

        return {
            "success": True,
            "message": "Payment verified successfully",
            "order_id": transaction.order_id,
            "payment_id": razorpay_payment_id,
            "amount": transaction.total_amount,
            "credits_purchased": transaction.credits_purchased,
            "razorpay_payment_link_id": razorpay_payment_link_id
        }

    @staticmethod
    async def handle_webhook(
        request: PaymentWebhookRequest
    ) -> Dict[str, Any]:
        """
        Handle webhook events from Razorpay.

        Args:
            request: Webhook request data

        Returns:
            Dict: Response indicating success or failure
        """
        logger.info(f"Handling webhook event: {request.event}")

        # Log the full event data for debugging
        logger.info(f"Full webhook event data: {request.dict()}")

        # Extract entities from webhook data
        event, payment_entity, order_entity, payment_link_entity = PaymentHandler._extract_webhook_entities(
            request.dict()
        )

        # Find the payment transaction
        transaction = PaymentHandler._find_transaction_from_webhook(
            payment_entity, payment_link_entity
        )

        if not transaction:
            error_msg = (
                f"Payment transaction not found for webhook event: {event}"
            )
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        logger.info(f"Found payment transaction: {transaction.order_id}")

        # Store webhook response
        PaymentHandler._store_webhook_response(transaction, event, request.dict())

        # Update transaction based on event type
        if event in ["payment.captured", "payment_link.paid", "order.paid"]:
            # These events indicate successful payment
            PaymentHandler._update_transaction_for_payment_captured(transaction, payment_entity)

            # Add credits to user if not already added
            user = UserModel.objects(id=transaction.user_id).first()
            if user:
                logger.info(f"User {user.id} current credits: {user.credits}")

                # Create an instance of UserLedgerTransactionHandler and call increase_credits
                ledger_handler = UserLedgerTransactionHandler()
                ledger_txn = ledger_handler.increase_credits(
                    str(user.id),
                    float(transaction.credits_purchased),
                    UserLedgerTransactionType.CREDIT.value
                )

                if ledger_txn:
                    # Refresh user object to get updated credits
                    user.reload()
                    logger.info(
                        f"Added {transaction.credits_purchased} credits to user {user.id}, "
                        f"new total: {user.credits}"
                    )
                else:
                    logger.error(f"Failed to create ledger transaction for user {user.id}")
            else:
                logger.error(f"User not found for ID: {transaction.user_id}")

        elif event == "payment.authorized":
            PaymentHandler._update_transaction_for_payment_authorized(transaction, payment_entity)

        elif event == "payment.failed":
            PaymentHandler._update_transaction_for_payment_failed(transaction, payment_entity)

        elif event == "payment.cancelled":
            PaymentHandler._update_transaction_for_payment_cancelled(transaction, payment_entity)

        else:
            logger.info(f"Unhandled webhook event type: {event}")

        return {"status": "success", "message": "Webhook processed successfully"}

    @staticmethod
    def _extract_webhook_entities(event_data: Dict[str, Any]) -> Tuple[str, Dict, Dict, Dict]:
        """
        Extract entities from webhook event data.

        Args:
            event_data: Webhook event data

        Returns:
            Tuple: (event_type, payment_entity, order_entity, payment_link_entity)
        """
        event = event_data.get("event", "")
        payment_entity = None
        order_entity = None
        payment_link_entity = None

        # Extract entities based on event type and structure
        if event == "payment_link.paid":
            # Structure for payment_link.paid event
            payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_entity = event_data.get("payload", {}).get("order", {}).get("entity", {})
            payment_link_entity = event_data.get("payload", {}).get("payment_link", {}).get("entity", {})
        elif event == "order.paid":
            # Structure for order.paid event
            payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_entity = event_data.get("payload", {}).get("order", {}).get("entity", {})
        else:
            # Structure for payment.* events
            payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})

        logger.info(f"Extracted payment entity: {payment_entity}")
        logger.info(f"Extracted order entity: {order_entity}")
        logger.info(f"Extracted payment link entity: {payment_link_entity}")

        return event, payment_entity or {}, order_entity or {}, payment_link_entity or {}

    @staticmethod
    def _find_transaction_from_webhook(
        payment_entity: Dict[str, Any],
        payment_link_entity: Dict[str, Any]
    ) -> Optional[PaymentTransaction]:
        """
        Find payment transaction from webhook data.

        Args:
            payment_entity: Payment entity from webhook
            payment_link_entity: Payment link entity from webhook

        Returns:
            Optional[PaymentTransaction]: Found transaction or None
        """
        # Try different identifiers to find the transaction
        payment_id = payment_entity.get("id")
        order_id = payment_entity.get("order_id")
        payment_link_id = payment_link_entity.get("id")

        logger.info(
            f"Looking for transaction with payment_id: {payment_id}, "
            f"order_id: {order_id}, payment_link_id: {payment_link_id}"
        )

        # Initialize repository
        payment_repository = PaymentRepository()

        # Try to find by payment_id first
        if payment_id:
            transaction = payment_repository.get_transaction_by_payment_id(payment_id)
            if transaction:
                logger.info(f"Found transaction by payment_id: {payment_id}")
                return transaction

        # Then try by order_id in Razorpay (which might be stored as razorpay_payment_link_id)
        if order_id:
            transaction = payment_repository.get_transaction_by_payment_link_id(order_id)
            if transaction:
                logger.info(f"Found transaction by order_id: {order_id}")
                return transaction

        # Finally try by payment_link_id
        if payment_link_id:
            transaction = payment_repository.get_transaction_by_payment_link_id(payment_link_id)
            if transaction:
                logger.info(f"Found transaction by payment_link_id: {payment_link_id}")
                return transaction

        return None

    @staticmethod
    def _store_webhook_response(
        transaction: PaymentTransaction,
        event: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Store webhook response in transaction.

        Args:
            transaction: Payment transaction
            event: Event type
            event_data: Webhook event data
        """
        # Initialize webhook_responses if not present
        if not transaction.webhook_responses:
            transaction.webhook_responses = {}

        # Add this webhook event to the responses
        webhook_key = f"{event}_{int(datetime.now(ist).timestamp())}"
        transaction.webhook_responses[webhook_key] = event_data

        # Save the transaction
        transaction.save()
        logger.info(f"Stored webhook response with key: {webhook_key}")

    @staticmethod
    def _update_transaction_for_payment_captured(
        transaction: PaymentTransaction,
        payment_entity: Dict[str, Any]
    ) -> None:
        """
        Update transaction for payment captured event.

        Args:
            transaction: Payment transaction
            payment_entity: Payment entity from webhook
        """
        payment_id = payment_entity.get("id")
        payment_method = payment_entity.get("method", "")

        # Update payment transaction using repository
        payment_repository = PaymentRepository()
        payment_repository.update_transaction_status(
            transaction.order_id, "paid", "captured"
        )

        # Update additional fields that aren't covered by update_transaction_status
        if payment_id and not transaction.payment_id:
            transaction.payment_id = payment_id
        if payment_method:
            transaction.payment_method = payment_method
        transaction.save()

        logger.info(f"Updated payment transaction status to 'paid' for order ID: {transaction.order_id}")

    @staticmethod
    def _update_transaction_for_payment_authorized(
        transaction: PaymentTransaction,
        payment_entity: Dict[str, Any]
    ) -> None:
        """
        Update transaction for payment authorized event.

        Args:
            transaction: Payment transaction
            payment_entity: Payment entity from webhook
        """
        payment_id = payment_entity.get("id")
        payment_method = payment_entity.get("method", "")

        # Update payment transaction using repository
        payment_repository = PaymentRepository()
        payment_repository.update_transaction_status(
            transaction.order_id, transaction.order_status, "authorized"
        )

        # Update additional fields that aren't covered by update_transaction_status
        if payment_id:
            transaction.payment_id = payment_id
        if payment_method:
            transaction.payment_method = payment_method
        transaction.save()

        logger.info(
            f"Updated payment transaction status to 'authorized' for order ID: {transaction.order_id}"
        )

    @staticmethod
    def _update_transaction_for_payment_failed(
        transaction: PaymentTransaction,
        payment_entity: Dict[str, Any]
    ) -> None:
        """
        Update transaction for payment failed event.

        Args:
            transaction: Payment transaction
            payment_entity: Payment entity from webhook
        """
        payment_id = payment_entity.get("id")
        payment_method = payment_entity.get("method", "")

        # Update payment transaction using repository
        payment_repository = PaymentRepository()
        payment_repository.update_transaction_status(
            transaction.order_id, "failed", "failed"
        )

        # Update additional fields that aren't covered by update_transaction_status
        if payment_id:
            transaction.payment_id = payment_id
        if payment_method:
            transaction.payment_method = payment_method
        transaction.save()

        logger.info(f"Updated payment transaction status to 'failed' for order ID: {transaction.order_id}")

    @staticmethod
    def _update_transaction_for_payment_cancelled(
        transaction: PaymentTransaction,
        payment_entity: Dict[str, Any]
    ) -> None:
        """
        Update transaction for payment cancelled event.

        Args:
            transaction: Payment transaction
            payment_entity: Payment entity from webhook
        """
        payment_id = payment_entity.get("id")
        payment_method = payment_entity.get("method", "")

        # Update payment transaction using repository
        payment_repository = PaymentRepository()
        payment_repository.update_transaction_status(
            transaction.order_id, "cancelled", "cancelled"
        )

        # Update additional fields that aren't covered by update_transaction_status
        if payment_id:
            transaction.payment_id = payment_id
        if payment_method:
            transaction.payment_method = payment_method
        transaction.save()

        logger.info(
            f"Updated payment transaction status to 'cancelled' for order ID: {transaction.order_id}"
        )

    @staticmethod
    async def manual_verify_payment(payment_link_id: str) -> Dict[str, Any]:
        """
        Manually verify a payment for testing purposes.

        Args:
            payment_link_id: Payment Link ID to verify

        Returns:
            Dict: Verification result
        """
        logger.info(f"Manual verification for payment link ID: {payment_link_id}")

        # Find the payment transaction
        transaction = PaymentTransaction.objects(razorpay_payment_link_id=payment_link_id).first()

        if not transaction:
            logger.error(f"Payment transaction not found for payment link ID: {payment_link_id}")
            return {
                "success": False,
                "message": "Payment transaction not found"
            }

        # Create a dummy payment ID
        payment_id = f"manual_pay_{uuid.uuid4().hex[:10]}"

        # Update payment transaction
        transaction.order_status = "paid"
        transaction.payment_status = "captured"
        transaction.payment_id = payment_id
        transaction.payment_method = "manual"
        transaction.signature = "manual_verification"
        transaction.save()
        logger.info("Updated payment transaction status to paid")

        # Add credits to user
        user = UserModel.objects(id=transaction.user_id).first()
        if not user:
            error_msg = f"User not found for ID: {transaction.user_id}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

        logger.info(f"User {user.id} current credits: {user.credits}")

        # Create an instance of UserLedgerTransactionHandler and call increase_credits
        ledger_handler = UserLedgerTransactionHandler()
        ledger_txn = ledger_handler.increase_credits(
            str(user.id),
            float(transaction.credits_purchased),
            UserLedgerTransactionType.CREDIT.value
        )

        if not ledger_txn:
            error_msg = "Failed to create ledger transaction"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

        # Refresh user object to get updated credits
        user.reload()

        logger.info(
            f"Added {transaction.credits_purchased} credits to user {user.id}, "
            f"new total: {user.credits}"
        )

        return {
            "success": True,
            "message": "Payment manually verified",
            "order_id": transaction.order_id,
            "payment_id": payment_id,
            "amount": transaction.total_amount,
            "credits_purchased": transaction.credits_purchased
        }
