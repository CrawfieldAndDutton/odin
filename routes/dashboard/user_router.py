# Standard library imports
from typing import Any

# Third-party library imports
from fastapi import APIRouter, Depends, status, security, HTTPException

# Local application imports
from dto.user_dto import (
    Token,
    TokenRefresh,
    ContactUsLead,
    User,
    UserCreate,
    UserUpdate,
    RefreshTokenRequest,
    UserOTPCreate,
    UserVerifyResponse,
    UserVerifyRequest
)
from dto.common_dto import APISuccessResponse

from handlers.auth_handlers import AuthHandler
from handlers.dashboard_handler import DashboardHandler
from handlers.user_ledger_transaction_handler import UserLedgerTransactionHandler
from dependencies.logger import logger

from models.user_model import User as UserModel

# Create a single router for all routes
auth_router = APIRouter(prefix="/dashboard/api/v1")

# Auth Routes


@auth_router.post("/auth/login", response_model=Token, tags=["Auth"])
def login(form_data: security.OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Authenticate a user and return an access token and refresh token.

    Args:
        form_data: OAuth2 password request form containing username and password.

    Returns:
        Token: Access token and refresh token.
    """
    return AuthHandler.login_user(form_data)


@auth_router.post("/auth/refresh", response_model=TokenRefresh, tags=["Auth"])
def refresh_token(token_data: RefreshTokenRequest) -> TokenRefresh:
    """
    Refresh an access token using a valid refresh token.

    Args:
        token_data: Refresh token request containing the refresh token.

    Returns:
        TokenRefresh: New access token and refresh token.
    """
    return AuthHandler.refresh_user_token(token_data)


@auth_router.post("/auth/logout", tags=["Auth"])
def logout(
    token_data: RefreshTokenRequest,
    current_user: UserModel = Depends(AuthHandler.get_current_user)
):
    """
    Log out a user and invalidate all their sessions.

    Args:
        token_data: Refresh token request containing the refresh token.
        current_user: Authenticated user.

    Returns:
        JSONResponse: Success or error message.
    """
    return AuthHandler.logout_user(token_data, current_user)


@auth_router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(user_data: UserCreate) -> User:
    """
    Register a new user.

    Args:
        user_data: User creation request containing user details.

    Returns:
        User: Details of the newly registered user.
    """
    return AuthHandler.register_new_user(user_data)

# User Routes


@auth_router.get("/users/me", response_model=User, tags=["Fetch Users"])
def read_users_me(
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> Any:
    """
    Get details of the currently authenticated user.

    Args:
        current_user: Authenticated user.

    Returns:
        User: Details of the currently authenticated user.
    """
    return AuthHandler.get_current_user_details(current_user)


@auth_router.put("/users/me", response_model=User, tags=["Fetch Users"])
def update_user_me(
    user_data: UserUpdate,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> Any:
    """
    Update details of the currently authenticated user.

    Args:
        user_data: User update request containing updated details.
        current_user: Authenticated user.

    Returns:
        User: Updated details of the currently authenticated user.
    """
    return AuthHandler.update_current_user(user_data, current_user)

# Dashboard Routes


@auth_router.get("/summary/fetch", response_model=APISuccessResponse, tags=["Dashboard"])
def get_summary(
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> APISuccessResponse:
    """
    Get summarized count of all services used by the user in the last 30 days.

    Args:
        current_user: Authenticated user.

    Returns:
        APISuccessResponse: Response containing service usage summary.

    Raises:
        HTTPException: If there's an error fetching the summary.
    """
    try:
        result = DashboardHandler().get_user_summarized_count(str(current_user.id))
        return APISuccessResponse(
            http_status_code=status.HTTP_200_OK,
            message="Successfully retrieved service usage summary",
            result=result
        )
    except Exception:
        logger.exception(f"Error fetching service usage summary for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch service usage summary",
            headers={"WWW-Authenticate": "Bearer"}
        )


@auth_router.get("/pending-credits/fetch", response_model=APISuccessResponse, tags=["Dashboard"])
def get_pending_credits(
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> APISuccessResponse:
    """
    Get total pending credits for the user.

    Args:
        current_user: Authenticated user.

    Returns:
        APISuccessResponse: Response containing pending credits information.

    Raises:
        HTTPException: If there's an error fetching pending credits.
    """
    try:
        result = DashboardHandler().get_user_pending_credits(str(current_user.id))
        return APISuccessResponse(
            http_status_code=status.HTTP_200_OK,
            message="Successfully retrieved pending credits",
            result={"pending_credits": result}
        )
    except Exception:
        logger.exception(f"Error fetching pending credits for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending credits",
            headers={"WWW-Authenticate": "Bearer"}
        )


@auth_router.get("/weekly-stats/fetch/{service_name}", response_model=APISuccessResponse, tags=["Dashboard"])
def get_weekly_stats(
    service_name: str,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> APISuccessResponse:
    """
    Get weekly statistics for a specific service used by the user.

    Args:
        service_name: Name of the service to get statistics for.
                     Example: "KYC_PAN", "KYC_AADHAAR"
        current_user: Authenticated user.

    Returns:
        APISuccessResponse: Response containing weekly statistics.

    Raises:
        HTTPException: If there's an error fetching weekly statistics.
    """
    try:
        result = DashboardHandler().get_user_weekly_statistics(str(current_user.id), service_name)
        return APISuccessResponse(
            http_status_code=status.HTTP_200_OK,
            message=f"Successfully retrieved weekly statistics for {service_name}",
            result=result
        )
    except Exception:
        logger.exception(f"Error fetching weekly statistics for user {current_user.id} and service {service_name}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch weekly statistics",
            headers={"WWW-Authenticate": "Bearer"}
        )


@auth_router.get("/ledger-history/fetch", response_model=APISuccessResponse, tags=["Dashboard"])
def get_ledger_history(
    page: int = 1,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> APISuccessResponse:
    """
    Get ledger history for the user.

    Args:
        page: Page number to get. (Each page contains 100 transactions)
        current_user: Authenticated user.

    Returns:
        APISuccessResponse: Response containing ledger history.

    Raises:
        HTTPException: If there's an error fetching ledger history.
    """
    try:
        result, total_transactions = UserLedgerTransactionHandler().get_user_ledger_transactions(
            str(current_user.id),
            page
        )
        return APISuccessResponse(
            http_status_code=status.HTTP_200_OK,
            message="Successfully retrieved ledger history",
            result={
                "ledger_transactions": result,
                "total_transactions": total_transactions
            }
        )
    except Exception:
        logger.exception(f"Error fetching ledger history for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ledger history",
            headers={"WWW-Authenticate": "Bearer"}
        )


@auth_router.post("/auth/send_otp", response_model=UserVerifyResponse, tags=["Auth"])
def send_otp(user: UserOTPCreate):
    """
    Send OTP (One-Time Password) to the user's email address for verification.

    Args:
        user (UserOTPCreate): User data containing email and phone number
                             Example: {"email": "user@example.com", "phone_number": "+1234567890"}

    Returns:
        UserVerifyResponse: Response containing email, verification status, and phone number
                          Example: {
                              "email": "user@example.com",
                              "is_email_verified": false,
                              "phone_number": "+1234567890"
                          }

    Raises:
        HTTPException:
            - 500: If there's an error sending the OTP
            - 400: If the email or phone number is invalid
    """
    logger.info(
        f"Received request with email: {user.email}, phone_number: {user.phone_number}"
    )
    try:
        AuthHandler.send_otp(user.email, user.phone_number)
        response_body = {
            "email": user.email,
            "is_email_verified": False,
            "phone_number": user.phone_number
        }
        logger.info(f"Response body: {response_body}")
        return response_body
    except Exception as e:
        # Log the error for debugging
        logger.exception(f"Error sending OTP: {str(e)}")
        # Handle any exceptions that may occur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send OTP: {str(e)}"
        )


@auth_router.post("/auth/verify_otp", response_model=UserVerifyResponse, tags=["Auth"])
def verify_otp(user: UserVerifyRequest):
    """
    Verify the OTP (One-Time Password) sent to the user's email.

    Args:
        user (UserVerifyRequest): User data containing email and OTP
                                Example: {"email": "user@example.com", "otp": "123456"}

    Returns:
        UserVerifyResponse: Response containing email and verification status
                          Example: {
                              "email": "user@example.com",
                              "is_email_verified": true
                          }

    Raises:
        HTTPException:
            - 400: If the OTP is invalid
            - 500: If there's an error verifying the OTP
    """
    logger.info(f"Received request with email: {user.email}, otp: {user.otp}")
    try:
        is_email_verified = AuthHandler.verify_otp(user.email, user.otp)
        if not is_email_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        response_body = {
            "email": user.email,
            "is_email_verified": True,
        }
        logger.info(f"Response body: {response_body}")
        return response_body
    except Exception as e:
        logger.exception(f"Error verifying OTP: {str(e)}")
        # Handle any exceptions that may occur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to verify OTP: {str(e)}"
        )


@auth_router.post("/contact-us/capture", response_model=APISuccessResponse, tags=["Dashboard"])
def capture_contact_us_lead(lead_data: ContactUsLead):
    """
    Capture and process a contact form submission from potential leads.

    Args:
        lead_data (ContactUsLead): Contact form data containing name, email, company, phone, and message
                                  Example: {
                                      "name": "John Doe",
                                      "email": "john@company.com",
                                      "company": "Company Inc",
                                      "phone": "+1234567890",
                                      "message": "Interested in your services"
                                  }

    Returns:
        APISuccessResponse: Response containing success status and result
                          Example: {
                              "http_status_code": 200,
                              "message": "Successfully captured contact us lead",
                              "result": true
                          }

    Raises:
        HTTPException:
            - 500: If there's an error processing the contact form
            - 400: If required fields are missing or invalid
    """
    try:
        result = DashboardHandler().capture_contact_us_lead(
            name=lead_data.name,
            lead_email=lead_data.email,
            company=lead_data.company,
            phone=lead_data.phone,
            message=lead_data.message
        )
        return APISuccessResponse(
            http_status_code=status.HTTP_200_OK,
            message="Successfully captured contact us lead",
            result=result
        )
    except ValueError as ve:
        logger.error(f"Validation error in contact form: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    except Exception as e:
        logger.exception("Error capturing contact us lead")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture contact us lead {str(e)}"
        )
