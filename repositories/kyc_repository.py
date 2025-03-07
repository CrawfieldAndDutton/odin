# Standard library imports
from typing import Optional

# Local application imports
from models.kyc_model import KYCValidationTransaction


class KYCRepository:
    @staticmethod
    def get_cached_record_vehicle(api_name: str, detail: dict, user_id: str) -> Optional[KYCValidationTransaction]:
        """
        Find a cached record for the given API name, identifier, and user_id.

        Args:
            api_name: Name of the API
            detail: Dictionary containing the reg_no
            user_id: ID of the user

        Returns:
            Optional[KYCValidationTransaction]: The cached record if found, None otherwise
        """
        return KYCValidationTransaction.objects(
            api_name=api_name,
            kyc_transaction_details__reg_no=detail["reg_no"],
            user_id=user_id,
        ).first()

    @staticmethod
    def get_cached_record_pan(api_name: str, detail: dict, user_id: str) -> Optional[KYCValidationTransaction]:
        """
        Find a cached record for the given API name, identifier, and user_id.

        Args:
            api_name: Name of the API
            detail: Dictionary containing the pan
            user_id: ID of the user

        Returns:
            Optional[KYCValidationTransaction]: The cached record if found, None otherwise
        """
        return KYCValidationTransaction.objects(
            api_name=api_name,
            kyc_transaction_details__pan=detail["pan"],
            user_id=user_id,
        ).first()

    @staticmethod
    def save_transaction(transaction: KYCValidationTransaction) -> None:
        """
        Save a KYC transaction to the database.

        Args:
            transaction: The KYC transaction to save

        Returns:
            None
        """
        transaction.save()
