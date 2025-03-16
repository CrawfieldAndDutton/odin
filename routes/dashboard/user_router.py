# Standard library imports
from typing import Any

# Third-party library imports
from fastapi import APIRouter, Depends, status, security, HTTPException

# Local application imports
from dto.user_dto import (
    Token,
    TokenRefresh,
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


@auth_router.post("/auth/send_otp", response_model=UserVerifyResponse)
def send_otp(user: UserOTPCreate):
    try:
        # Log the request data for debugging
        logger.info(
            f"Received request with email: {user.email}, phone_number: {user.phone_number}"
        )

        AuthHandler.send_otp(user.email, user.phone_number)
        return {
            "email": user.email,
            "is_verified": False,
            "phone_number": user.phone_number
        }
    except Exception as e:
        # Log the error for debugging
        logger.exception(f"Error sending OTP: {str(e)}")
        # Handle any exceptions that may occur
        raise HTTPException(
            status_code=500, detail=f"Failed to send OTP: {str(e)}"
        )


@auth_router.post("/auth/verify_otp", response_model=UserVerifyResponse,)
def verify_otp(user: UserVerifyRequest):
    try:
        is_verified = AuthHandler.verify_otp(user.email, user.otp)
        if not is_verified:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Get the user to include phone_number in response
        from repositories.user_repository import UserRepository
        user_data = UserRepository.find_user_by_email(user.email)

        return {
            "email": user.email,
            "is_verified": True,
            "phone_number": user_data.phone_number
        }
    except Exception as e:
        # Handle any exceptions that may occur
        raise HTTPException(
            status_code=500, detail=f"Failed to verify OTP: {str(e)}"
        )
