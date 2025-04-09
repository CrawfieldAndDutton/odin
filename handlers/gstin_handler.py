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

from services.scraper_services import GSTINService

from scrapers.gstin_scraper import GSTINScraper


class GSTINHandler:

    def __init__(self):
        self.user_repository = UserRepository()
        self.kyc_repository = KYCRepository()
        self.user_ledger_transaction_handler = UserLedgerTransactionHandler()

    def get_gstin_kyc_details(self, gstin: str, user_id: str) -> Tuple[dict, int]:
        """
        Get GSTIN KYC details, first checking cache then API.

        Args:
            gstin: GSTIN to verify
            user_id: ID of the user making the request

        Returns:
            dict: GSTIN verification details
        """
        # Check if user has sufficient credits
        if self.user_repository.get_user_by_id(user_id).credits < ServicePricing.KYB_GSTIN_COST:
            logger.error(f"User {user_id} has insufficient credits to verify GSTIN {gstin}")
            raise InsufficientCreditsException()

        transaction = self.kyc_repository.create_kyc_validation_transaction(
            user_id=user_id,
            api_name=UserLedgerTransactionType.KYB_GSTIN.value,
            status="ERROR",
            provider_name=KYCProvider.INTERNAL.value,
            http_status_code=500
        )
        start_time = time.time()
        # Step 1: Check if the GSTIN is already cached
        cached_details = self.__get_gstin_kyc_details_from_db(gstin)
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
            gstin_verification_response = cached_details.kyc_provider_response

        else:
            # Step 2: If not cached, get from API
            gstin_verification_response = self.__get_gstin_kyc_details_from_api(gstin, transaction)

        if transaction.status in getattr(KYCServiceBillableStatus, UserLedgerTransactionType.KYB_GSTIN.value):
            self.user_ledger_transaction_handler.deduct_credits(
                user_id, UserLedgerTransactionType.KYB_GSTIN.value, f"{transaction.status}|{gstin}")

        return gstin_verification_response, transaction.http_status_code

    def __get_gstin_kyc_details_from_db(self, gstin: str) -> Optional[KYCValidationTransaction]:
        """
        Get GSTIN details from database cache.

        Args:
            gstin: GSTIN to verify

        Returns:
            Optional[KYCValidationTransaction]: Cached GSTIN details or None if not found
        """
        try:
            transaction = self.kyc_repository.get_kyc_validation_transaction(
                api_name=UserLedgerTransactionType.KYB_GSTIN.value,
                identifier=gstin,
                kyc_service_billable_status=KYCServiceBillableStatus.KYB_GSTIN
            )
            if transaction and transaction.kyc_provider_response:
                logger.info(f"Cache hit for GSTIN {gstin}")
                return transaction
            return None
        except Exception as e:
            logger.error(f"Error fetching gstin {gstin} from cache: {str(e)}")
            return None

    def __get_gstin_kyc_details_from_api(self, gstin: str, transaction: KYCValidationTransaction) -> dict:
        """
        Get GSTIN details from external API.

        Args:
            gstin: GSTIN to verify
            transaction: KYC validation transaction object

        Returns:
            dict: gstin verification details from API
        """
        try:
            # Call external API
            logger.info(f"Calling GSTIN API for {gstin}")
            response, tat = GSTINService.call_external_api(gstin)
            external_response = GSTINScraper.extract_gst_data(response, gstin)
            print(external_response)

            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=response.status_code,
                tat=tat,
                message=external_response.get("message", "GSTIN NOT FOUND"),
                kyc_transaction_details={"gstin": gstin},
                kyc_provider_request={"gstin": gstin},
                kyc_provider_response=external_response,
                status=self.__determine_status(response.status_code),
                is_cached=False,
                provider_name=KYCProvider.AITAN.value
            )
            return external_response

        except Exception as e:
            logger.error(f"Error fetching GSTIN {gstin} from API: {str(e)}")
            raise e

    def __determine_status(self, http_status_code: int) -> str:
        """
        Determine the status of the GSTIN verification.

        Args:
            http_status_code: HTTP status code of the API response

        Returns:
            str: Status of the GSTIN verification
        """
        status = "ERROR"
        if http_status_code == 200:
            return "FOUND"
        elif http_status_code == 400:
            return "BAD_REQUEST"
        elif http_status_code == 404:
            return "NOT_FOUND"
        elif http_status_code == 429:
            return "TOO_MANY_REQUESTS"
        elif http_status_code == 503:
            return "SOURCE_DOWN"

        return status
