from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from mongoengine.errors import DoesNotExist
from dependencies.logger import logger
from dependencies.config import Config as settings
from dependencies.exceptions import CredentialsException, UserNotFoundException
from models.user_model import User as UserModel
from dto.user_dto import TokenPayload


class AuthHandler:
    """Authentication and authorization handler for the application."""

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
        """
        Decode JWT token and retrieve the current user.

        Args:
            token: JWT token extracted from the Authorization header

        Returns:
            UserModel: The current authenticated user

        Raises:
            CredentialsException: If token is invalid
            UserNotFoundException: If user doesn't exist
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            if token_data.sub is None or token_data.type != "access":
                raise CredentialsException()
        except JWTError:
            logger.exception("Error decoding token")
            raise CredentialsException()

        try:
            user = UserModel.objects.get(id=token_data.sub)
        except DoesNotExist:
            logger.exception("User not found")
            raise UserNotFoundException()

        return user

    @staticmethod
    async def get_current_active_user(
        current_user: UserModel = Depends(get_current_user)
    ) -> UserModel:
        """
        Check if the current user is active.

        Args:
            current_user: The current authenticated user

        Returns:
            UserModel: The current active user

        Raises:
            HTTPException: If user is inactive
        """
        # current_user is a coroutine, so we need to await it
        user = await current_user
        if not user.is_active:
            logger.exception("Inactive user")
            raise HTTPException(status_code=400, detail="Inactive user")
        return user

    @staticmethod
    async def get_current_admin_user(
        current_user: UserModel = Depends(get_current_active_user)
    ) -> UserModel:
        """
        Check if the current user has admin role.

        Args:
            current_user: The current active user

        Returns:
            UserModel: The current admin user

        Raises:
            HTTPException: If user doesn't have admin role
        """
        # current_user is a coroutine, so we need to await it
        user = await current_user
        if user.role != "admin":
            logger.exception("Not enough permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user


# Create class-level references to the static methods for easier importing
get_current_user = AuthHandler.get_current_user
get_current_active_user = AuthHandler.get_current_active_user
get_current_admin_user = AuthHandler.get_current_admin_user
