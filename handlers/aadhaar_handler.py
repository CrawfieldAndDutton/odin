# Standard library imports
from typing import Tuple, Optional
import time

# Local application imports
from dependencies.configuration import KYCProvider, ServicePricing, UserLedgerTransactionType, KYCServiceBillableStatus
from dependencies.exceptions import InsufficientCreditsException
from dependencies.logger import logger

from handlers.user_ledger_transaction_handler import UserLedgerTransactionHandler

from models.kyc_model import KYCValidationTransaction

from repositories.user_repository import UserRepository
from repositories.kyc_repository import KYCRepository

from services.aitan_services import AadhaarService


class AadhaarHandler:

    def __init__(self):
        self.user_repository = UserRepository()
        self.kyc_repository = KYCRepository()
        self.user_ledger_transaction_handler = UserLedgerTransactionHandler()

    def get_aadhaar_kyc_details(self, aadhaar: str, user_id: str) -> Tuple[dict, int]:
        """
        Get Aadhaar KYC details, first checking cache then API.

        Args:
            aadhaar: Aadhaar number to verify
            user_id: ID of the user making the request

        Returns:
            dict: Aadhaar verification details
        """
        # Check if user has sufficient credits
        if self.user_repository.get_user_by_id(user_id).credits < ServicePricing.KYC_AADHAAR_COST:
            logger.error(f"User {user_id} has insufficient credits to verify Aadhaar {aadhaar}")
            raise InsufficientCreditsException()

        transaction = self.kyc_repository.create_kyc_validation_transaction(
            user_id=user_id,
            api_name=UserLedgerTransactionType.KYC_AADHAAR.value,
            status="ERROR",
            provider_name=KYCProvider.INTERNAL.value,
            http_status_code=500
        )
        start_time = time.time()
        # Step 1: Check if the Aadhaar is already cached
        cached_details = self.__get_aadhaar_kyc_details_from_db(aadhaar)
        if cached_details:
            # Calculate the time taken to fetch from cache
            tat = (time.time() - start_time)
            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=cached_details.http_status_code,
                tat=tat,
                message=cached_details.message,
                kyc_transaction_details=cached_details.kyc_transaction_details,
                kyc_provider_request=cached_details.kyc_provider_request,
                kyc_provider_response=cached_details.kyc_provider_response,
                status=cached_details.status,
                is_cached=True,
                provider_name=KYCProvider.INTERNAL.value
            )
            aadhaar_verification_response = cached_details.kyc_provider_response

        else:
            # Step 2: If not cached, get from API
            aadhaar_verification_response = self.__get_aadhaar_kyc_details_from_api(
                aadhaar, transaction)

        if transaction.status in getattr(KYCServiceBillableStatus, UserLedgerTransactionType.KYC_AADHAAR.value):
            self.user_ledger_transaction_handler.deduct_credits(
                user_id, UserLedgerTransactionType.KYC_AADHAAR.value, f"{transaction.status}|{aadhaar}")

        return aadhaar_verification_response, transaction.http_status_code

    def __get_aadhaar_kyc_details_from_db(self, aadhaar: str) -> Optional[KYCValidationTransaction]:
        """
        Get Aadhaar details from database cache.

        Args:
            aadhaar: Aadhaar number to verify

        Returns:
            Optional[KYCValidationTransaction]: Cached Aadhaar details or None if not found
        """
        try:
            transaction = self.kyc_repository.get_kyc_validation_transaction(
                api_name=UserLedgerTransactionType.KYC_AADHAAR.value,
                identifier=aadhaar,
                kyc_service_billable_status=KYCServiceBillableStatus.KYC_AADHAAR
            )
            if transaction and transaction.kyc_provider_response:
                logger.info(f"Cache hit for Aadhaar {aadhaar}")
                return transaction
            return None
        except Exception as e:
            logger.error(f"Error fetching Aadhaar {aadhaar} from cache: {str(e)}")
            return None

    def __get_aadhaar_kyc_details_from_api(self, aadhaar: str, transaction: KYCValidationTransaction) -> dict:
        """
        Get Aadhaar details from external API.

        Args:
            aadhaar: Aadhaar number to verify
            transaction: KYC validation transaction object

        Returns:
            dict: Aadhaar verification details from API
        """
        try:
            # Call external API
            logger.info(f"Calling Aadhaar API for {aadhaar}")
            response, tat = AadhaarService.call_external_api(aadhaar)
            external_response = response.json()

            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=response.status_code,
                tat=tat,
                message=external_response.get("message", "No message provided"),
                kyc_transaction_details={"aadhaar": aadhaar},
                kyc_provider_request={"aadhaar": aadhaar},
                kyc_provider_response=external_response,
                status=self.__determine_status(response.status_code, external_response.get("status_code", 0)),
                is_cached=False,
                provider_name=KYCProvider.AITAN.value
            )
            return external_response

        except Exception as e:
            logger.error(f"Error fetching Aadhaar {aadhaar} from API: {str(e)}")
            raise e

    def __determine_status(self, http_status_code: int, response_status_code: int) -> str:
        """
        Determine the status of the Aadhaar verification.

        Args:
            http_status_code: HTTP status code of the API response
            response_status_code: Status code of the API response

        Returns:
            str: Status of the Aadhaar verification
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
        elif http_status_code == 503:
            status = "SOURCE_DOWN"

        return status
