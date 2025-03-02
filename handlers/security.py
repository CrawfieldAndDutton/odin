from datetime import datetime, timedelta
from typing import Any, Optional, Union, Tuple

from jose import jwt
from passlib.context import CryptContext
import secrets

from dependencies.config import settings
from models.user_model import RefreshToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> Tuple[str, datetime]:
    # Create a secure random token
    token_value = secrets.token_hex(32)

    # Set expiration date
    expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

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
        to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, expires_at


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_refresh_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
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
            expires_at__gt=datetime.utcnow()
        ).first()

        if not stored_token:
            return None

        return user_id

    except jwt.JWTError:
        return None


def revoke_refresh_token(token: str) -> bool:
    try:
        payload = jwt.decode(
            token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        jti = payload.get("jti")
        if not jti:
            return False

        # Find and revoke the token
        stored_token = RefreshToken.objects(token=jti).first()
        if stored_token:
            stored_token.revoked = True
            stored_token.save()
            return True

        return False

    except jwt.JWTError:
        return False
