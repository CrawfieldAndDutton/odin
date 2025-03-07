# Standard library imports
from typing import Any

# Third-party library imports
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

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
auth_router = APIRouter()

# Auth Routes


@auth_router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Authenticate a user and return an access token and refresh token.
    """
    return await AuthHandler.login_user(form_data)


@auth_router.post("/auth/refresh", response_model=TokenRefresh, tags=["Auth"])
async def refresh_token(token_data: RefreshTokenRequest) -> TokenRefresh:
    """
    Refresh an access token using a valid refresh token.
    """
    return await AuthHandler.refresh_user_token(token_data)


@auth_router.post("/auth/logout", tags=["Auth"])
async def logout(
    token_data: RefreshTokenRequest,
    current_user: UserModel = Depends(AuthHandler.get_current_user)
):
    """
    Log out a user and invalidate all their sessions.
    """
    return await AuthHandler.logout_user(token_data, current_user)


@auth_router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user_data: UserCreate) -> User:
    """
    Register a new user.
    """
    return await AuthHandler.register_new_user(user_data)

# User Routes


@auth_router.get("/users/me", response_model=User, tags=["Fetch Users"])
async def read_users_me(
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> Any:
    """
    Get details of the currently authenticated user.
    """
    return await AuthHandler.get_current_user_details(current_user)


@auth_router.put("/users/me", response_model=User, tags=["Fetch Users"])
async def update_user_me(
    user_data: UserUpdate,
    current_user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> Any:
    """
    Update details of the currently authenticated user.
    """
    return await AuthHandler.update_current_user(user_data, current_user)
