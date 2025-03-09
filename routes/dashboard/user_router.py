# Standard library imports
from typing import Any

# Third-party library imports
from fastapi import APIRouter, Depends, status, security

# Local application imports
from dto.user_dto import (
    Token,
    TokenRefresh,
    User,
    UserCreate,
    UserUpdate,
    RefreshTokenRequest,
)

from handlers.auth_handlers import AuthHandler

from models.user_model import User as UserModel

# Create a single router for all routes
auth_router = APIRouter(prefix="/dashboard/api/v1")

# Auth Routes


@auth_router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: security.OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Authenticate a user and return an access token and refresh token.

    Args:
        form_data: OAuth2 password request form containing username and password.

    Returns:
        Token: Access token and refresh token.
    """
    return await AuthHandler.login_user(form_data)


@auth_router.post("/auth/refresh", response_model=TokenRefresh, tags=["Auth"])
async def refresh_token(token_data: RefreshTokenRequest) -> TokenRefresh:
    """
    Refresh an access token using a valid refresh token.

    Args:
        token_data: Refresh token request containing the refresh token.

    Returns:
        TokenRefresh: New access token and refresh token.
    """
    return await AuthHandler.refresh_user_token(token_data)


@auth_router.post("/auth/logout", tags=["Auth"])
async def logout(
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
    return await AuthHandler.logout_user(token_data, current_user)


@auth_router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user_data: UserCreate) -> User:
    """
    Register a new user.

    Args:
        user_data: User creation request containing user details.

    Returns:
        User: Details of the newly registered user.
    """
    return await AuthHandler.register_new_user(user_data)

# User Routes


@auth_router.get("/users/me", response_model=User, tags=["Fetch Users"])
async def read_users_me(
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> Any:
    """
    Get details of the currently authenticated user.

    Args:
        current_user: Authenticated user.

    Returns:
        User: Details of the currently authenticated user.
    """
    return await AuthHandler.get_current_user_details(current_user)


@auth_router.put("/users/me", response_model=User, tags=["Fetch Users"])
async def update_user_me(
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
    return await AuthHandler.update_current_user(user_data, current_user)
