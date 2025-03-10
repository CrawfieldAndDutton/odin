from typing import Tuple

from dependencies.configuration import KYCProvider, ServicePricing, UserLedgerTransactionType
from dependencies.exceptions import InsufficientCreditsException
from dependencies.logger import logger

from handlers.user_ledger_transaction_handler import UserLedgerTransactionHandler

from models.kyc_model import KYCValidationTransaction

from repositories.user_repository import UserRepository
from repositories.kyc_repository import KYCRepository

from services.aitan_services import PanService


class PanHandler:

    def __init__(self):
        self.user_repository = UserRepository()
        self.kyc_repository = KYCRepository()
        self.user_ledger_transaction_handler = UserLedgerTransactionHandler()

    def get_pan_kyc_details(self, pan: str, user_id: str) -> Tuple[dict, int]:
        """
        Get PAN KYC details, first checking cache then API.

        Args:
            pan: PAN number to verify
            user_id: ID of the user making the request

        Returns:
            dict: PAN verification details
        """
        # Check if user has sufficient credits
        if not self.user_repository.get_user_by_id(user_id).credits >= ServicePricing.KYC_PAN_COST:
            logger.error(f"User {user_id} has insufficient credits to verify PAN {pan}")
            raise InsufficientCreditsException()

        transaction = self.kyc_repository.create_kyc_validation_transaction(
            user_id=user_id,
            api_name=UserLedgerTransactionType.KYC_PAN.value,
            status="ERROR",
            provider_name=KYCProvider.INTERNAL.value
        )

        # Step 1: Check if the PAN is already cached
        cached_details = self.__get_pan_kyc_details_from_db(pan)
        if cached_details:
            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=cached_details.http_status_code,
                tat=cached_details.tat,
                message=cached_details.message,
                kyc_transaction_details=cached_details.kyc_transaction_details,
                kyc_provider_request=cached_details.kyc_provider_request,
                kyc_provider_response=cached_details.kyc_provider_response,
                status=cached_details.status,
                is_cached=True,
                provider_name=KYCProvider.INTERNAL.value
            )
            pan_verification_response = cached_details.kyc_provider_response

        else:
            # Step 2: If not cached, get from API
            pan_verification_response = self.__get_pan_kyc_details_from_api(pan, transaction)

        if transaction.status == "FOUND":
            self.user_ledger_transaction_handler.deduct_credits(user_id, UserLedgerTransactionType.KYC_PAN.value)

        return pan_verification_response, transaction.http_status_code

    def __get_pan_kyc_details_from_db(self, pan: str) -> dict:
        """
        Get PAN details from database cache.

        Args:
            pan: PAN number to verify

        Returns:
            dict: Cached PAN details or None if not found
        """
        try:
            transaction = self.kyc_repository.get_kyc_validation_transaction(
                api_name=UserLedgerTransactionType.KYC_PAN.value,
                identifier=pan,
                status="FOUND"
            )
            if transaction and transaction.kyc_provider_response:
                logger.info(f"Cache hit for PAN {pan}")
                return transaction
            return None
        except Exception as e:
            logger.error(f"Error fetching PAN {pan} from cache: {str(e)}")
            return None

    def __get_pan_kyc_details_from_api(self, pan: str, transaction: KYCValidationTransaction) -> dict:
        """
        Get PAN details from external API.

        Args:
            pan: PAN number to verify
            transaction: KYC validation transaction object

        Returns:
            dict: PAN verification details from API
        """
        try:
            # Call external API
            response, tat = PanService.call_external_api(pan)
            external_response = response.json()

            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=response.status_code,
                tat=tat,
                message=external_response.get("message", "No message provided"),
                kyc_transaction_details={"pan": pan},
                kyc_provider_request={"pan": pan},
                kyc_provider_response=external_response,
                status=self.__determine_status(response.status_code, external_response.get("status_code", 0)),
                is_cached=False,
                provider_name=KYCProvider.AITAN.value
            )
            return external_response

        except Exception as e:
            logger.error(f"Error fetching PAN {pan} from API: {str(e)}")
            raise e

    def __determine_status(self, http_status_code: int, response_status_code: int) -> str:
        """
        Determine the status of the PAN verification.

        Args:
            http_status_code: HTTP status code of the API response
            response_status_code: Status code of the API response

        Returns:
            str: Status of the PAN verification
        """
        status = "ERROR"
        if http_status_code == 200:
            if response_status_code == 100:
                status = "FOUND"
            elif response_status_code == 101:
                status = "FOUND"
            elif response_status_code == 102:
                status = "NOT_FOUND"
            else:
                status = "ERROR"
        elif http_status_code == 400:
            status = "BAD_REQUEST"

        return status
