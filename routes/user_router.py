from typing import Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pytz import timezone
from dependencies.logger import logger
from dependencies.config import Config
from dependencies.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_refresh_token,
    delete_refresh_token,
    delete_all_user_tokens
)
from dto.user_dto import (
    Token,
    TokenRefresh,
    User,
    UserCreate,
    UserUpdate,
    RefreshTokenRequest
)
from dependencies.exceptions import UserAlreadyExistsException
from handlers.auth_handlers import get_current_active_user, get_current_user
from repositories.user_repository import UserRepository
from models.user_model import User as UserModel


ist = timezone('Asia/Kolkata')


# Create a single router for all routes
router = APIRouter()

# Auth Routes


@router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Authenticate a user and return an access token and refresh token.
    """
    user = UserRepository.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.error("Incorrect username or password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.is_active = True
    user.save()

    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=str(user.id), expires_delta=access_token_expires)
    refresh_token, expires_at = create_refresh_token(user_id=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_at": datetime.now(ist) + access_token_expires
    }


@router.post("/auth/refresh", response_model=TokenRefresh, tags=["Auth"])
async def refresh_token(token_data: RefreshTokenRequest) -> TokenRefresh:
    """
    Refresh an access token using a valid refresh token.
    """
    user_id = verify_refresh_token(token_data.refresh_token)
    if not user_id:
        logger.exception("Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user_id, expires_delta=access_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": datetime.now() + access_token_expires
    }


@router.post("/auth/logout", tags=["Auth"])
async def logout(token_data: RefreshTokenRequest, current_user: UserModel = Depends(get_current_user)):
    delete_refresh_token(token_data.refresh_token)
    delete_all_user_tokens(str(current_user.id))
    current_user.is_active = False
    current_user.save()
    return {"detail": "Successfully logged out and all sessions terminated"}


@router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user_data: UserCreate) -> User:
    """
    Register a new user.
    """
    if UserRepository.get_user_by_email(user_data.email):
        logger.info("User with this email already exists")
        raise UserAlreadyExistsException()

    if UserRepository.get_user_by_username(user_data.username):
        logger.error("Username already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user = UserRepository.create_user(user_data)

    return User(
        _id=str(user.id),
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# User Routes


@router.get("/users/me", response_model=User, tags=["Fetch Users"])
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)) -> Any:
    """
    Get details of the currently authenticated user.
    """
    return User(
        _id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        created_at=current_user.created_at
    )


@router.put("/users/me", response_model=User, tags=["Fetch Users"])
async def update_user_me(
    user_data: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Update details of the currently authenticated user.
    """
    updated_user = UserRepository.update_user(current_user, user_data)

    return User(
        _id=str(updated_user.id),
        email=updated_user.email,
        username=updated_user.username,
        is_active=updated_user.is_active,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        created_at=updated_user.created_at
    )
