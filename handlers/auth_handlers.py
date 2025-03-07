# Standard library imports
from datetime import datetime, timedelta
import secrets
from typing import Any, Optional, Union, Tuple, Dict

# Third-party library imports
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from mongoengine.errors import DoesNotExist
from pytz import timezone

# Local application imports
from dependencies.logger import logger
from dependencies.config import Config as settings
from repositories.user_repository import UserRepository
from dependencies.exceptions import CredentialsException, UserNotFoundException, UserAlreadyExistsException
from models.user_model import User as UserModel, RefreshToken
from dto.user_dto import TokenPayload, UserCreate, UserUpdate, Token, TokenRefresh, User, RefreshTokenRequest
from dependencies.password_utils import PasswordUtils

ist = timezone('Asia/Kolkata')


class AuthHandler:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

    @staticmethod
    def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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
    def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if not current_user.is_active:
            logger.exception("Inactive user")
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    @staticmethod
    def get_current_admin_user(current_user: UserModel = Depends(get_current_active_user)) -> UserModel:
        if current_user.role != "admin":
            logger.exception("Not enough permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"

            )
        return current_user

    @staticmethod
    def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        expire = datetime.now(ist) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str) -> Tuple[str, datetime]:
        token_value = secrets.token_hex(32)
        expires_at = datetime.now(ist) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = RefreshToken(user_id=user_id, token=token_value, expires_at=expires_at)
        refresh_token.save()

        to_encode = {"exp": expires_at, "sub": str(user_id), "jti": token_value, "type": "refresh"}
        encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)

        return encoded_jwt, expires_at

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return PasswordUtils.verify_password(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return PasswordUtils.get_password_hash(password)

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            jti = payload.get("jti")
            if not user_id or not jti:
                return None

            stored_token = RefreshToken.objects(
                token=jti,
                user_id=user_id,
                expires_at__gt=datetime.now(ist)
            ).first()

            if not stored_token:
                return None

            return user_id
        except JWTError:
            logger.exception("Error decoding refresh token")
            return None

    @staticmethod
    def delete_refresh_token(token: str) -> bool:
        try:
            payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            user_id = payload.get("sub")
            if not jti or not user_id:
                return False

            result = RefreshToken.objects(token=jti).delete()
            return result > 0
        except JWTError:
            logger.exception("Error decoding refresh token")
            return False

    @staticmethod
    def delete_all_user_tokens(user_id: str) -> bool:
        result = RefreshToken.objects(user_id=user_id, expires_at__gt=datetime.now(ist)).delete()
        return result > 0

    @staticmethod
    async def login_user(form_data: OAuth2PasswordRequestForm) -> Token:

        user = UserRepository.get_user_by_username(form_data.username)
        if not user or not PasswordUtils.verify_password(form_data.password, user.hashed_password):
            logger.error("Incorrect username or password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user.is_active = True
        user.save()

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthHandler.create_access_token(subject=str(user.id), expires_delta=access_token_expires)
        refresh_token, expires_at = AuthHandler.create_refresh_token(
            user_id=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": datetime.now(ist) + access_token_expires
        }

    @staticmethod
    async def refresh_user_token(token_data: RefreshTokenRequest) -> TokenRefresh:
        user_id = AuthHandler.verify_refresh_token(token_data.refresh_token)
        if not user_id:
            logger.exception("Invalid refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthHandler.create_access_token(subject=user_id, expires_delta=access_token_expires)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": datetime.now(ist) + access_token_expires
        }

    @staticmethod
    async def logout_user(token_data: RefreshTokenRequest, current_user: UserModel) -> Dict[str, str]:
        AuthHandler.delete_refresh_token(token_data.refresh_token)
        AuthHandler.delete_all_user_tokens(str(current_user.id))
        current_user.is_active = False
        current_user.save()
        return {"detail": "Successfully logged out and all sessions terminated"}

    @staticmethod
    async def register_new_user(user_data: UserCreate) -> User:

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

    @staticmethod
    async def get_current_user_details(current_user: UserModel) -> User:
        return User(
            _id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
            is_active=current_user.is_active,
            role=current_user.role,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at
        )

    @staticmethod
    async def update_current_user(user_data: UserUpdate, current_user: UserModel) -> User:

        updated_user = UserRepository.update_user(current_user, user_data)

        return User(
            _id=str(updated_user.id),
            email=updated_user.email,
            username=updated_user.username,
            is_active=updated_user.is_active,
            role=updated_user.role,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
