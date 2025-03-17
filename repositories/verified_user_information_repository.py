from mongoengine.queryset.visitor import Q
from mongoengine.errors import DoesNotExist, ValidationError

from dependencies.logger import logger
from models.user_model import VerifiedUserInformation


class VerifiedUserInformationRepository:
    """Repository for handling verified user information operations."""

    def get_user_by_email_or_phone_number(self, email: str, phone_number: str):
        """
        Retrieve a user by either their email or phone number.

        Args:
            email (str): The email address to search for
            phone_number (str): The phone number to search for

        Returns:
            VerifiedUserInformation or None: The user if found, None otherwise
        """
        try:
            return VerifiedUserInformation.objects(Q(email=email) | Q(phone_number=phone_number)).first()
        except DoesNotExist:
            logger.info(f"No user found with email {email} or phone number {phone_number}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving user with email {email} or phone number {phone_number}: {str(e)}")
            return None

    @staticmethod
    def create_verified_user_information(email: str, phone_number: str, otp: str):
        """
        Create a new verified user information record.

        Args:
            email (str): The user's email address
            phone_number (str): The user's phone number
            otp (str): The one-time password for verification

        Returns:
            VerifiedUserInformation: The newly created user information record

        Raises:
            ValidationError: If the data is invalid
            Exception: For other database errors
        """
        try:
            # Create new user if doesn't exist
            user = VerifiedUserInformation(email=email, phone_number=phone_number, otp=otp)
            user.save()
            logger.info(f"Successfully created verified user information for email: {email}")
            return user
        except ValidationError as ve:
            logger.error(f"Validation error creating verified user information: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error creating verified user information: {str(e)}")
            raise

    @staticmethod
    def find_user_by_email(email: str):
        """
        Find a user by their email address.

        Args:
            email (str): The email address to search for

        Returns:
            VerifiedUserInformation or None: The user if found, None otherwise
        """
        try:
            return VerifiedUserInformation.objects(email=email).first()
        except DoesNotExist:
            logger.info(f"No user found with email: {email}")
            return None
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {str(e)}")
            return None
