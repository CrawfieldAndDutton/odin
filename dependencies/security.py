import secrets
from datetime import datetime, timedelta
from typing import Any, Optional, Union, Tuple
from pytz import timezone
from passlib.context import CryptContext
from jose import jwt
from dependencies.config import Config
from models.user_model import RefreshToken
from dependencies.logger import logger
# Define IST timezone
ist = timezone('Asia/Kolkata')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(ist) + expires_delta
    else:
        expire = datetime.now(ist) + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> Tuple[str, datetime]:
    # Create a secure random token
    token_value = secrets.token_hex(32)

    # Set expiration date in IST
    expires_at = datetime.now(ist) + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)

    # Create token in database
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token_value,
        expires_at=expires_at
    )
    refresh_token.save()

    # Create JWT with reference to the token
    to_encode = {
        "exp": expires_at,
        "sub": str(user_id),
        "jti": token_value,
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(
        to_encode, Config.REFRESH_SECRET_KEY, algorithm=Config.ALGORITHM)

    return encoded_jwt, expires_at


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_refresh_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, Config.REFRESH_SECRET_KEY, algorithms=[Config.ALGORITHM]
        )

        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id or not jti:
            return None

        # Check if token exists and is not revoked
        stored_token = RefreshToken.objects(
            token=jti,
            user_id=user_id,
            revoked=False,
            expires_at__gt=datetime.now(ist)  # Use IST timezone
        ).first()

        if not stored_token:
            return None

        return user_id

    except jwt.JWTError:
        logger.exception("Error decoding refresh token")
        return None


def delete_refresh_token(token: str) -> bool:
    """Delete a refresh token from the database"""
    try:
        payload = jwt.decode(
            token, Config.REFRESH_SECRET_KEY, algorithms=[Config.ALGORITHM]
        )

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            return False

        # Find and delete the token
        result = RefreshToken.objects(token=jti).delete()
        return result > 0

    except jwt.JWTError:
        logger.exception("Error decoding refresh token")
        return False


def delete_all_user_tokens(user_id: str) -> bool:
    """Delete all refresh tokens for a specific user"""
    result = RefreshToken.objects(
        user_id=user_id,
        expires_at__gt=datetime.now(ist)
    ).delete()
    return result > 0
