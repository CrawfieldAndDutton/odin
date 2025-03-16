# Standard library imports
from typing import Dict, Any, Optional

# Third-party library imports
import razorpay
from fastapi import APIRouter, Depends, HTTPException, responses

# Local application imports
from handlers.payment_handler import PaymentHandler
from handlers.auth_handlers import AuthHandler

from models.user_model import User as UserModel

from dto.payment_dto import (
    PaymentLinkRequest,
    PaymentLinkResponse,
    PaymentWebhookRequest,
)

from dependencies.logger import logger
from dependencies.configuration import AppConfiguration

# Create router
payment_router = APIRouter(prefix="/dashboard/api/v1/payments", tags=["payments"])


@payment_router.post("/create", response_model=PaymentLinkResponse)
def create_payment_link(
    request: PaymentLinkRequest,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> PaymentLinkResponse:
    """
    Create a payment link for purchasing credits.

    Args:
        request: Payment link request
        current_user: Authenticated user

    Returns:
        PaymentLinkResponse: Payment link details
    """
    try:
        reference_id, response = PaymentHandler.create_payment_link(request, current_user)

        return PaymentLinkResponse(
            order_id=reference_id,
            short_url=response.get("short_url"),
            amount=request.amount,
            credits_purchased=request.credits_purchased,
            status="pending"
        )
    except razorpay.errors.BadRequestError as e:
        # Handle Razorpay-specific errors
        logger.error(f"Razorpay BadRequestError: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment link creation failed: {str(e)}")
    except Exception as e:
        # Let FastAPI handle other exceptions
        logger.error(f"Error creating payment link: {str(e)}")
        raise


@payment_router.get("/verify")
def verify_payment(
    razorpay_payment_id: str,
    razorpay_payment_link_id: str,
    razorpay_signature: str,
    razorpay_payment_link_reference_id: Optional[str] = None,
    razorpay_payment_link_status: Optional[str] = None
) -> responses.RedirectResponse:
    """
    Verify a payment from Razorpay callback and redirect to a success/failure page.

    Returns:
        RedirectResponse: Redirect to success or failure page
    """
    try:
        logger.info(f"CALLBACK RECEIVED: payment_id={razorpay_payment_id}, link_id={razorpay_payment_link_id}")
        logger.info(f"Payment status from Razorpay: {razorpay_payment_link_status}")
        logger.info(f"Payment signature: {razorpay_signature}")
        logger.info(f"Payment link reference ID: {razorpay_payment_link_reference_id}")

        # Check if payment was canceled or failed based on status from Razorpay
        if (razorpay_payment_link_status and
                razorpay_payment_link_status.lower() not in ["paid", "authorized", "captured"]):
            logger.warning(f"Payment was not successful. Status: {razorpay_payment_link_status}")
            # Redirect to a failure page
            redirect_url = f"{AppConfiguration.FRONTEND_BASE_URL}/#/failure-payment"
            logger.info(f"Redirecting to failure page: {redirect_url}")
            return responses.RedirectResponse(url=redirect_url, status_code=303)

        # Get the verification response directly from the handler
        response = PaymentHandler.verify_payment(
            razorpay_payment_id=razorpay_payment_id,
            razorpay_payment_link_id=razorpay_payment_link_id,
            razorpay_signature=razorpay_signature,
            razorpay_payment_link_reference_id=razorpay_payment_link_reference_id,
            razorpay_payment_link_status=razorpay_payment_link_status
        )

        logger.info(f"VERIFICATION RESULT: {response}")

        # Determine the redirect URL based on the verification result
        if response.success:  # Check the 'success' field
            # Redirect to a success page
            logger.info(f"VERIFICATION RESULT: {response}")
            redirect_url = f"{AppConfiguration.FRONTEND_BASE_URL}/#/success-payment"
            logger.info(f"Redirecting to success page: {redirect_url}")
        else:
            # Redirect to a failure page
            logger.info(f"VERIFICATION RESULT: {response}")
            redirect_url = f"{AppConfiguration.FRONTEND_BASE_URL}/#/failure-payment"
            logger.info(f"Redirecting to failure page: {redirect_url}")

        # Perform the redirect
        return responses.RedirectResponse(url=redirect_url, status_code=303)
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay BadRequestError: {str(e)}")
        redirect_url = f"{AppConfiguration.FRONTEND_BASE_URL}/#/failure-payment"
        return responses.RedirectResponse(url=redirect_url, status_code=303)
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        redirect_url = f"{AppConfiguration.FRONTEND_BASE_URL}/#/failure-payment"
        return responses.RedirectResponse(url=redirect_url, status_code=303)


@payment_router.post("/manual-verify/{payment_link_id}")
def manual_verify_payment(
    payment_link_id: str
) -> Dict[str, Any]:
    """
    Manually verify a payment for testing purposes.

    Args:
        payment_link_id: The ID of the payment link to verify

    Returns:
        Dict[str, Any]: Result of the manual verification
    """
    try:
        logger.info(f"Manual verification for payment link ID: {payment_link_id}")

        result = PaymentHandler.manual_verify_payment(payment_link_id)

        if not result["success"]:
            logger.error(f"Manual verification failed: {result.get('message')}")
            raise HTTPException(status_code=400, detail=result.get('message'))

        return result
    except HTTPException as e:
        # Re-raise FastAPI HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Error in manual verification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Manual verification failed: {str(e)}")


@payment_router.post("/webhook", response_model=Dict[str, Any])
def handle_webhook(request: PaymentWebhookRequest) -> Dict[str, Any]:
    """
    Handle webhook events from Razorpay.

    Returns:
        Dict[str, Any]: Result of the webhook processing
    """
    try:
        logger.info(f"Received webhook event: {request.event}")

        result = PaymentHandler.handle_webhook(request)

        if result.get("status") != "success":
            logger.error(f"Webhook processing failed: {result.get('message')}")
            # We still return a 200 status to Razorpay to acknowledge receipt
            # but include the error details in the response

        return result
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return a 200 status even on error to acknowledge receipt to Razorpay
        # but include error details in the response
        return {"status": "error", "message": f"Webhook processing failed: {str(e)}"}
