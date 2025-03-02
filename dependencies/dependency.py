from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from mongoengine.errors import DoesNotExist

from dependencies.config import settings
from handlers.exceptions import CredentialsException, UserNotFoundException
from models.user_model import User as UserModel
from dto.user_dto import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if token_data.sub is None or token_data.type != "access":
            raise CredentialsException()
    except JWTError:
        raise CredentialsException()

    try:
        user = UserModel.objects.get(id=token_data.sub)
    except DoesNotExist:
        raise UserNotFoundException()

    return user


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Additional dependency to check admin role
async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
