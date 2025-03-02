from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Any
from mongoengine.errors import DoesNotExist

from dependencies.config import settings
from handlers.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_refresh_token,
    revoke_refresh_token,
    get_password_hash
)
from models.user_model import User as UserModel
from dto.user_dto import (
    Token,
    TokenRefresh,
    User,
    UserCreate,
    UserUpdate,
    RefreshTokenRequest
)
from handlers.exceptions import UserAlreadyExistsException
from dependencies.dependency import get_current_active_user

# Create a single router for all routes
router = APIRouter()


# Auth Routes
@router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Authenticate a user and return an access token and refresh token.
    """
    try:
        user = UserModel.objects.get(username=form_data.username)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token, expires_at = create_refresh_token(user_id=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_at": datetime.now() + access_token_expires
    }


@router.post("/auth/refresh", response_model=TokenRefresh, tags=["Auth"])
async def refresh_token(token_data: RefreshTokenRequest) -> TokenRefresh:
    """
    Refresh an access token using a valid refresh token.
    """
    user_id = verify_refresh_token(token_data.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user_id, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": datetime.now() + access_token_expires
    }


@router.post("/auth/logout", tags=["Auth"])
async def logout(token_data: RefreshTokenRequest):
    """
    Revoke a refresh token to log out the user.
    """
    success = revoke_refresh_token(token_data.refresh_token)

    if not success:
        return {"detail": "Token not found or already revoked"}

    return {"detail": "Successfully logged out"}


@router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user_data: UserCreate) -> User:
    """
    Register a new user.
    """
    # Check if user already exists
    existing_email = UserModel.objects(email=user_data.email).first()
    if existing_email:
        raise UserAlreadyExistsException()

    existing_username = UserModel.objects(username=user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user
    user = UserModel(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        # Set role, default to "user"
        role=user_data.role if hasattr(user_data, 'role') else "user"
    )
    user.save()

    # Convert MongoDB document to Pydantic model
    return User(
        _id=str(user.id),
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        role=user.role,  # Include role in response
        first_name=user.first_name,
        last_name=user.last_name,
        created_at=user.created_at,
        updated_at=user.updated_at  # Include updated_at in response
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
    # Update user fields
    if user_data.email is not None:
        current_user.email = user_data.email
    if user_data.username is not None:
        current_user.username = user_data.username
    if user_data.first_name is not None:
        current_user.first_name = user_data.first_name
    if user_data.last_name is not None:
        current_user.last_name = user_data.last_name
    if user_data.password is not None:
        current_user.hashed_password = get_password_hash(user_data.password)

    current_user.save()

    return User(
        _id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        created_at=current_user.created_at
    )
