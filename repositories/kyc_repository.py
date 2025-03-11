# Standard library imports
from typing import Optional, Union

# Third-party library imports
from mongoengine import DoesNotExist

# Local application imports
from dependencies.logger import logger
from dependencies.configuration import UserLedgerTransactionType
from models.kyc_model import KYCValidationTransaction


class KYCRepository:

    def get_kyc_validation_transaction(
        self, api_name: str, identifier: str, http_status_code: Union[int, list[int]]
    ) -> Optional[KYCValidationTransaction]:
        try:
            # Ensure http_status_code is a list
            if isinstance(http_status_code, int):
                http_status_code = [http_status_code]
            if api_name == UserLedgerTransactionType.KYC_PAN.value:
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    kyc_transaction_details__pan=identifier,
                    http_status_code__in=http_status_code,
                ).first()
            elif api_name == UserLedgerTransactionType.KYC_RC.value:
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    kyc_transaction_details__reg_no=identifier,
                    http_status_code__in=http_status_code,
                ).first()
            elif api_name == UserLedgerTransactionType.KYC_VOTER.value:
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    kyc_transaction_details__epic_no=identifier,
                    http_status_code__in=http_status_code,
                ).first()
            elif api_name == UserLedgerTransactionType.KYC_AADHAAR.value:
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    kyc_transaction_details__aadhaar_no=identifier,
                    http_status_code__in=http_status_code,
                ).first()
            elif api_name == UserLedgerTransactionType.KYC_DL.value:
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    kyc_transaction_details__dl_no=identifier,
                    http_status_code__in=http_status_code,
                ).first()
            elif api_name == UserLedgerTransactionType.KYC_PASSPORT.value:
                return KYCValidationTransaction.objects(
                    api_name=api_name,
                    kyc_transaction_details__file_number=identifier,
                    http_status_code__in=http_status_code,
                ).first()
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting KYC validation transaction {api_name} with {identifier}: {str(e)}")
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
