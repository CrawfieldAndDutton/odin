# Standard library imports
from typing import Optional

# Third-party library imports
from mongoengine.errors import DoesNotExist

# Local application imports
from models.api_client_model import APIClient as APIClientModel


class APIClientRepository:
    """Repository for API client-related database operations."""

    @staticmethod
    def get_api_client(client_id: str) -> Optional[APIClientModel]:
        """
        Get an API client by client_id.

        Args:
            client_id: The client_id to search for

        Returns:
            APIClientModel or None: The API client if found, None otherwise
        """
        try:
            return APIClientModel.objects.get(client_id=client_id)
        except DoesNotExist:
            return None

    @staticmethod
    def deduct_credit(api_client: APIClientModel, deduction_value: float) -> APIClientModel:
        """
        Deduct credits from an API client's balance.

        Args:
            api_client: The API client to deduct credits from
            deduction_value: The amount of credits to deduct

        Returns:
            APIClientModel: The updated API client
        """
        if api_client.credits < deduction_value:
            raise ValueError("Insufficient credits")
        
        api_client.credits -= deduction_value
        api_client.save()
        return api_client 