# Standard library imports
from typing import Optional

# Third-party library imports
from mongoengine.errors import DoesNotExist

# Local application imports
from models.api_client_model import APIClient as APIClientModel
from models.user_model import User as UserModel


class APIClientRepository:
    """Repository for API client-related database operations."""

    @staticmethod
    def get_api_client(client_id: str) -> Optional[UserModel]:
        """
        Get the associated user for an API client by client_id.

        Args:
            client_id: The client_id to search for

        Returns:
            Optional[UserModel]: The associated user if found, None otherwise
        """
        try:
            api_client = APIClientModel.objects.get(client_id=client_id)
            return UserModel.objects.get(id=api_client.user_id)
        except DoesNotExist:
            return None 