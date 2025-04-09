# Standard library imports
from typing import Optional

# Third-party library imports
from mongoengine import DoesNotExist

# Local application imports
from dependencies.logger import logger
from dependencies.configuration import KYCRepositoryConfig

from models.kyc_model import KYCValidationTransaction


class KYCRepository:

    def get_kyc_validation_transaction(
        self,
        api_name: str,
        identifier: str,
        kyc_service_billable_status: list[str]
    ) -> Optional[KYCValidationTransaction]:
        """Get KYC validation transaction by type and identifier."""
        try:
            # Handle special cases
            if KYCRepositoryConfig.is_special_case(api_name):
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    __raw__={
                        "$or": [
                            {"kyc_transaction_details.uan": identifier},
                            {"kyc_transaction_details.pan": identifier},
                            {"kyc_transaction_details.mobile": identifier},
                            {"kyc_transaction_details.dob": identifier},
                            {"kyc_transaction_details.employer_name": identifier},
                            {"kyc_transaction_details.employee_name": identifier}
                        ]
                    },
                    status__in=kyc_service_billable_status,
                ).first()

            # Standard KYC case
            field_name = KYCRepositoryConfig.get_field_name(api_name)
            if field_name:
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    **{f'kyc_transaction_details__{field_name}': identifier},
                    status__in=kyc_service_billable_status,
                ).first()

            return None

        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting KYC transaction {api_name}: {str(e)}")
            raise e

    def create_kyc_validation_transaction(
        self,
        user_id: str,
        api_name: str,
        status: str,
        provider_name: str,
        http_status_code: int
    ) -> KYCValidationTransaction:
        """
        Create a new KYC validation transaction.

        Args:
            user_id: ID of the user
            api_name: Name of the API (e.g., KYC_PAN, KYC_RC)
            status: Transaction status
            provider_name: Name of the provider

        Returns:
            Created KYCValidationTransaction object
        """
        try:
            transaction = KYCValidationTransaction(
                user_id=user_id,
                api_name=api_name,
                status=status,
                provider_name=provider_name,
                http_status_code=http_status_code
            )
            transaction.save()
            logger.info(f"Created KYC validation transaction for user {user_id} with API {api_name}")
            return transaction
        except Exception as e:
            logger.error(f"Error creating KYC validation transaction: {str(e)}")
            raise e

    def update_kyc_validation_transaction(
        self,
        kyc_validation_transaction: KYCValidationTransaction,
        **kwargs
    ) -> KYCValidationTransaction:
        """
        Update an existing KYC validation transaction.

        Args:
            kyc_validation_transaction: Transaction to update
            **kwargs: Fields to update

        Returns:
            Updated KYCValidationTransaction object
        """
        try:
            for key, value in kwargs.items():
                setattr(kyc_validation_transaction, key, value)
            kyc_validation_transaction.save()
            logger.info(f"Updated KYC validation transaction {kyc_validation_transaction.id}")
            return kyc_validation_transaction
        except Exception as e:
            logger.error(f"Error updating KYC validation transaction: {str(e)}")
            raise e
