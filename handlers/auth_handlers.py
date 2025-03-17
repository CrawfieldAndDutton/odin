# Standard library imports
from datetime import datetime, timedelta
import secrets
import base64
from typing import Any, Optional, Union, Tuple, Dict
import random

# Third-party library imports
from fastapi import Depends, HTTPException, status, security, Header
from jose import jwt, JWTError
from mongoengine.errors import DoesNotExist

# Local application imports
from dependencies.logger import logger
from dependencies.configuration import AppConfiguration
from dependencies.password_utils import PasswordUtils
from dependencies.exceptions import CredentialsException, UserNotFoundException, UserAlreadyExistsException
from dependencies.constants import IST

from dto.user_dto import TokenPayload, UserCreate, UserUpdate, Token, TokenRefresh, User, RefreshTokenRequest

from repositories.user_repository import UserRepository
from repositories.api_client_repository import APIClientRepository
from repositories.verified_user_information_repository import VerifiedUserInformationRepository

from models.user_model import User as UserModel, RefreshToken
from models.api_client_model import APIClient as APIClientModel

from services.email_service import EmailService


class AuthHandler:
    oauth2_scheme = security.OAuth2PasswordBearer(tokenUrl="/dashboard/api/v1/auth/login")

    @staticmethod
    def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
        """
        Retrieve the current authenticated user from the JWT token.

        Args:
            token: JWT token provided in the request header.

        Returns:
            UserModel: The authenticated user.

        Raises:
            CredentialsException: If the token is invalid or expired.
            UserNotFoundException: If the user does not exist.
        """
        try:
            payload = jwt.decode(token, AppConfiguration.SECRET_KEY, algorithms=[AppConfiguration.ALGORITHM])
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
        """
        Retrieve the current authenticated user if they are active.

        Args:
            current_user: The authenticated user.

        Returns:
            UserModel: The active authenticated user.

        Raises:
            HTTPException: If the user is inactive.
        """
        if not current_user.is_active:
            logger.exception("Inactive user")
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    @staticmethod
    def get_current_admin_user(current_user: UserModel = Depends(get_current_active_user)) -> UserModel:
        """
        Retrieve the current authenticated user if they are an admin.

        Args:
            current_user: The authenticated user.

        Returns:
            UserModel: The admin user.

        Raises:
            HTTPException: If the user does not have admin privileges.
        """
        if current_user.role != "admin":
            logger.exception("Not enough permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user

    @staticmethod
    def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            subject: The subject of the token (usually the user ID).
            expires_delta: Optional expiration time delta.

        Returns:
            str: The encoded JWT access token.
        """
        expire = datetime.now(IST) + (expires_delta or timedelta(minutes=AppConfiguration.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
        encoded_jwt = jwt.encode(to_encode, AppConfiguration.SECRET_KEY, algorithm=AppConfiguration.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str) -> Tuple[str, datetime]:
        """
        Create a JWT refresh token and store it in the database.

        Args:
            user_id: The ID of the user for whom the refresh token is created.

        Returns:
            Tuple[str, datetime]: The encoded JWT refresh token and its expiration time.
        """
        token_value = secrets.token_hex(32)
        expires_at = datetime.now(IST) + timedelta(days=AppConfiguration.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = RefreshToken(user_id=user_id, token=token_value, expires_at=expires_at)
        refresh_token.save()

        to_encode = {"exp": expires_at, "sub": str(user_id), "jti": token_value, "type": "refresh"}
        encoded_jwt = jwt.encode(to_encode, AppConfiguration.REFRESH_SECRET_KEY, algorithm=AppConfiguration.ALGORITHM)

        return encoded_jwt, expires_at

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.

        Args:
            plain_password: The plain text password to verify.
            hashed_password: The hashed password to compare against.

        Returns:
            bool: True if the passwords match, False otherwise.
        """
        return PasswordUtils.verify_password(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generate a hash for a given password.

        Args:
            password: The plain text password to hash.

        Returns:
            str: The hashed password.
        """
        return PasswordUtils.get_password_hash(password)

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[str]:
        """
        Verify the validity of a refresh token.

        Args:
            token: The refresh token to verify.

        Returns:
            Optional[str]: The user ID if the token is valid, otherwise None.
        """
        try:
            payload = jwt.decode(token, AppConfiguration.REFRESH_SECRET_KEY, algorithms=[AppConfiguration.ALGORITHM])
            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            jti = payload.get("jti")
            if not user_id or not jti:
                return None

            stored_token = RefreshToken.objects(
                token=jti,
                user_id=user_id,
                expires_at__gt=datetime.now(IST)
            ).first()

            if not stored_token:
                return None

            return user_id
        except JWTError:
            logger.exception("Error decoding refresh token")
            return None

    @staticmethod
    def delete_refresh_token(token: str) -> bool:
        """
        Delete a refresh token from the database.

        Args:
            token: The refresh token to delete.

        Returns:
            bool: True if the token was deleted, False otherwise.
        """
        try:
            payload = jwt.decode(token, AppConfiguration.REFRESH_SECRET_KEY, algorithms=[AppConfiguration.ALGORITHM])
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
        """
        Delete all refresh tokens for a specific user.

        Args:
            user_id: The ID of the user whose tokens should be deleted.

        Returns:
            bool: True if tokens were deleted, False otherwise.
        """
        result = RefreshToken.objects(user_id=user_id, expires_at__gt=datetime.now(IST)).delete()
        return result > 0

    @staticmethod
    def login_user(form_data: security.OAuth2PasswordRequestForm) -> Token:
        """
        Authenticate a user and return access and refresh tokens.

        Args:
            form_data: The login form data containing username and password.

        Returns:
            Token: The access and refresh tokens.

        Raises:
            HTTPException: If the credentials are invalid.
        """
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

        access_token_expires = timedelta(minutes=AppConfiguration.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthHandler.create_access_token(subject=str(user.id), expires_delta=access_token_expires)
        refresh_token, _ = AuthHandler.create_refresh_token(user_id=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": datetime.now(IST) + access_token_expires
        }

    @staticmethod
    def refresh_user_token(token_data: RefreshTokenRequest) -> TokenRefresh:
        """
        Refresh a user's access token using their refresh token.

        Args:
            token_data: The refresh token request data.

        Returns:
            TokenRefresh: The new access token.

        Raises:
            HTTPException: If the refresh token is invalid.
        """
        user_id = AuthHandler.verify_refresh_token(token_data.refresh_token)
        if not user_id:
            logger.exception("Invalid refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=AppConfiguration.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthHandler.create_access_token(subject=user_id, expires_delta=access_token_expires)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": datetime.now(IST) + access_token_expires
        }

    @staticmethod
    def logout_user(token_data: RefreshTokenRequest, current_user: UserModel) -> Dict[str, str]:
        """
        Logout a user by invalidating their refresh token.

        Args:
            token_data: The refresh token request data.
            current_user: The current authenticated user.

        Returns:
            Dict[str, str]: A message indicating successful logout.
        """
        if token_data.refresh_token:
            AuthHandler.delete_refresh_token(token_data.refresh_token)
            AuthHandler.delete_all_user_tokens(str(current_user.id))
            return {"message": "Successfully logged out"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )

    @staticmethod
    def register_new_user(user_data: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_data: The user creation request containing user details.

        Returns:
            User: Details of the newly registered user.

        Raises:
            UserAlreadyExistsException: If a user with the same email already exists.
            HTTPException: If the username is already registered, email is not verified, or phone number is already
            registered.
        """

        # Check if email is verified
        verified_user = VerifiedUserInformationRepository.find_user_by_email(user_data.email)
        if not verified_user or not verified_user.is_email_verified:
            logger.error(f"Email {user_data.email} is not verified")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is not verified. Please verify your email first.",
            )

        # Check for existing email

        if UserRepository.get_user_by_email(user_data.email):
            logger.info("User with this email already exists")
            raise UserAlreadyExistsException()

        # Check for existing username
        if UserRepository.get_user_by_username(user_data.username):
            logger.error("Username already registered")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        # Check for existing phone number
        if UserRepository.get_user_by_phone_number(user_data.phone_number):
            logger.error("Phone number already registered")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )

        user = UserRepository.create_user(user_data)
        return User(
            _id=str(user.id),
            email=user.email,
            username=user.username,
            phone_number=user.phone_number,
            is_active=user.is_active,
            role=user.role,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    @staticmethod
    def get_current_user_details(current_user: UserModel) -> User:
        """
        Get the current user's details.

        Args:
            current_user: The current authenticated user.

        Returns:
            User: The user's details.
        """
        return User(
            _id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
            phone_number=current_user.phone_number,
            is_active=current_user.is_active,
            role=current_user.role,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at
        )

    @staticmethod
    def update_current_user(user_data: UserUpdate, current_user: UserModel) -> User:
        """
        Update the current user's details.

        Args:
            user_data: The user update data.
            current_user: The current authenticated user.

        Returns:
            User: The updated user.
        """
        updated_user = UserRepository.update_user(current_user, user_data)

        return User(
            _id=str(updated_user.id),
            email=updated_user.email,
            username=updated_user.username,
            phone_number=updated_user.phone_number,
            is_active=updated_user.is_active,
            role=updated_user.role,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )

    @staticmethod
    def get_current_client(token: str) -> UserModel:
        """
        Retrieve the associated user from the BasicAuth token.

        Args:
            token: BasicAuth token provided in the request header.

        Returns:
            UserModel: The associated user.

        Raises:
            CredentialsException: If the token is invalid or client not found.
        """
        try:
            # Decode BasicAuth token
            credentials = base64.b64decode(token.split(" ")[1]).decode("utf-8")
            client_id, client_secret = credentials.split(":")

            # Get API client
            api_client = APIClientModel.objects.get(client_id=client_id)
            if not api_client:
                logger.error("API client not found")
                raise CredentialsException()

            # Verify client secret
            if api_client.client_secret != client_secret:
                logger.error("Invalid client secret")
                raise CredentialsException()

            # Check if client is enabled
            if not api_client.is_enabled:
                logger.error("API client is disabled")
                raise CredentialsException()

            # Get associated user
            user = APIClientRepository.get_api_client(client_id)
            if not user:
                logger.error("Associated user not found")
                raise CredentialsException()

            return user
        except Exception as e:
            logger.exception(f"Unexpected error in get_current_client: {str(e)}")
            raise CredentialsException()

    @staticmethod
    def get_api_client(authorization: str = Header(...)) -> UserModel:
        """
        Get the API client from the authorization header.

        Args:
            authorization: The authorization header value.

        Returns:
            UserModel: The API client user.

        Raises:
            HTTPException: If the authorization header is invalid.
        """
        return AuthHandler.get_current_client(authorization)

    @staticmethod
    def generate_otp():
        """
        Generate a random 6-digit OTP (One-Time Password).

        Returns:
            str: A 6-digit OTP as a string
        """
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_otp(email: str, phone_number: str):
        """
        Send OTP to a user's email for verification.

        Args:
            email (str): The user's email address to send the OTP to
            phone_number (str): The user's phone number for record keeping

        Raises:
            Exception: If there's an error sending the email or saving to database
        """
        # First check if user already exists
        user_repository = UserRepository()
        if user_repository.get_user_by_email(email):
            logger.error(f"User with email {email} already exists")
            raise UserAlreadyExistsException()
        if user_repository.get_user_by_phone_number(phone_number):
            logger.error(f"User with phone number {phone_number} already exists")
            raise UserAlreadyExistsException()

        otp = AuthHandler.generate_otp()
        verified_user_information_repository = VerifiedUserInformationRepository()
        verified_user_information_obj = verified_user_information_repository.get_user_by_email_or_phone_number(
            email, phone_number
        )
        if verified_user_information_obj:
            verified_user_information_obj.otp = otp
            verified_user_information_obj.is_email_verified = False
            verified_user_information_obj.save()
        else:
            verified_user_information_obj = verified_user_information_repository.create_verified_user_information(
                email, phone_number, otp
            )

        EmailService.send_otp_email(email, otp)

    @staticmethod
    def verify_otp(email: str, otp: str):
        """
        Verify a user's OTP and mark their email as verified if correct.

        This function:
        1. Retrieves the user's stored OTP
        2. Compares it with the provided OTP
        3. If matched, marks the email as verified
        4. Returns success/failure status

        Args:
            email (str): The user's email address to verify
            otp (str): The OTP to verify against the stored value

        Returns:
            bool: True if OTP is valid and verification successful, False otherwise

        Raises:
            ValueError: If email or OTP is empty or invalid
            Exception: If there's an error during verification process
        """
        try:
            # Validate inputs
            if not email or not otp:
                logger.error("Email or OTP is empty")
                raise ValueError("Email and OTP are required")

            # Get user information from repository
            verified_user_information_obj = VerifiedUserInformationRepository.find_user_by_email(email)
            if not verified_user_information_obj:
                logger.error(f"No user found with email: {email}")
                return False

            # Verify OTP
            if verified_user_information_obj.otp != otp:
                logger.error(f"Invalid OTP for email: {email}")
                return False

            # Mark email as verified
            verified_user_information_obj.is_email_verified = True
            verified_user_information_obj.save()

            logger.info(f"Successfully verified email: {email}")
            return True

        except ValueError as ve:
            logger.error(f"Validation error in verify_otp: {str(ve)}")
            raise
        except Exception as e:
            logger.exception(f"Error verifying OTP for email {email}: {str(e)}")
            raise Exception(f"Failed to verify OTP: {str(e)}")
