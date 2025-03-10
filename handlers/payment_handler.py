# Standard library imports
from typing import Dict, Any

# Third-party library imports
from fastapi import HTTPException, Depends

# Local application imports
from dependencies.logger import logger
from handlers.auth_handlers import AuthHandler
from models.user_model import User as UserModel
from services.payment_service import PaymentService
from dto.payment_dto import (
    PaymentLinkRequest,
    PaymentLinkResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    PaymentWebhookRequest,
    PaymentStatusResponse
)


class PaymentHandler:
    """Handler for payment-related operations."""

    @staticmethod
    async def create_payment_link(
        request: PaymentLinkRequest,
        current_user: UserModel = Depends(AuthHandler.get_current_active_user)
    ) -> PaymentLinkResponse:
        """
        Create a payment link for the user.

        Args:
            request: Payment link request data
            current_user: Current authenticated user

        Returns:
            PaymentLinkResponse: Payment link details
        """
        try:
            logger.info(f"Creating payment link for user {current_user.id} for {request.credits_purchased} credits")

            # Validate request
            if request.amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be greater than zero")

            if request.credits_purchased <= 0:
                raise HTTPException(status_code=400, detail="Credits must be greater than zero")

            # Create payment link
            result = await PaymentService.create_payment_link(
                user=current_user,
                amount=request.amount,
                credits_purchased=request.credits_purchased
            )

            return PaymentLinkResponse(
                order_id=result["order_id"],
                short_url=result["short_url"],
                amount=result["amount"],
                credits_purchased=result["credits_purchased"],
                status=result["status"]
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create payment link")

    @staticmethod
    async def verify_payment(
        request: PaymentVerificationRequest
    ) -> PaymentVerificationResponse:
        """
        Verify a payment from Razorpay callback.

        Args:
            request: Payment verification request data

        Returns:
            PaymentVerificationResponse: Verification result
        """
        try:
            logger.info("====================== PAYMENT HANDLER STARTED ======================")
            logger.info(f"Handler verifying payment with ID {request.razorpay_payment_id}")
            logger.info(f"Payment link ID: {request.razorpay_payment_link_id}")

            # Verify payment
            result = await PaymentService.verify_payment(
                razorpay_payment_id=request.razorpay_payment_id,
                razorpay_payment_link_id=request.razorpay_payment_link_id,
                razorpay_signature=request.razorpay_signature
            )

            logger.info(f"Verification result: {result}")

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

            logger.info(f"Handler response: {response}")
            logger.info("====================== PAYMENT HANDLER COMPLETED ======================")
            return response

        except Exception as e:
            logger.error("====================== PAYMENT HANDLER ERROR ======================")
            logger.error(f"Error in payment handler: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return PaymentVerificationResponse(
                success=False,
                message=f"Payment verification failed: {str(e)}"
            )

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
        try:
            logger.info(f"Handling webhook event: {request.event}")

            # Process webhook
            success = await PaymentService.handle_webhook(request.dict())

            if success:
                return {"status": "success", "message": "Webhook processed successfully"}
            else:
                return {"status": "error", "message": "Failed to process webhook"}

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {"status": "error", "message": f"Webhook processing failed: {str(e)}"}

    @staticmethod
    async def get_payment_status(
        order_id: str,
        current_user: UserModel = Depends(AuthHandler.get_current_active_user)
    ) -> PaymentStatusResponse:
        """
        Get the status of a payment.

        Args:
            order_id: Order ID to check
            current_user: Current authenticated user

        Returns:
            PaymentStatusResponse: Payment status details
        """
        try:
            logger.info(f"Getting payment status for order {order_id}")

            # Get payment status
            result = await PaymentService.get_payment_status(order_id)

            if not result:
                raise HTTPException(status_code=404, detail="Order not found")

            return PaymentStatusResponse(
                order_id=result["order_id"],
                status=result["status"],
                amount=result["amount"],
                credits_purchased=result["credits_purchased"],
                payment_id=result.get("payment_id"),
                created_at=result["created_at"],
                updated_at=result["updated_at"]
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get payment status")
