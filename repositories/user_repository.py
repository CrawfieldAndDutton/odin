from typing import Optional
from mongoengine.errors import DoesNotExist
from models.user_model import User as UserModel
from dto.user_dto import UserCreate, UserUpdate
from dependencies.security import get_password_hash


class UserRepository:

    @staticmethod
    def get_user_by_username(username: str) -> Optional[UserModel]:
        try:
            return UserModel.objects.get(username=username)
        except DoesNotExist:
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[UserModel]:
        return UserModel.objects(email=email).first()

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[UserModel]:
        return UserModel.objects.get(id=user_id)

    @staticmethod
    def create_user(user_data: UserCreate) -> UserModel:
        user = UserModel(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role if hasattr(user_data, 'role') else "user"
        )
        user.save()
        return user

    @staticmethod
    def update_user(user: UserModel, user_data: UserUpdate) -> UserModel:
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        user.save()
        return user
