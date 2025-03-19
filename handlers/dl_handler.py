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

from services.aitan_services import DLService


class DLHandler:

    def __init__(self):
        self.user_repository = UserRepository()
        self.kyc_repository = KYCRepository()
        self.user_ledger_transaction_handler = UserLedgerTransactionHandler()

    def get_dl_kyc_details(self, dl_no: str, dob: str, user_id: str) -> Tuple[dict, int]:
        """
        Get DL KYC details, first checking cache then API.

        Args:
            dl_no: DL number to verify
            dob: DOB to verify
            user_id: ID of the user making the request

        Returns:
            dict: DL verification details
        """
        # Check if user has sufficient credits
        if self.user_repository.get_user_by_id(user_id).credits < ServicePricing.KYC_DL_COST:
            logger.error(f"User {user_id} has insufficient credits to verify DL {dl_no}")
            raise InsufficientCreditsException()

        transaction = self.kyc_repository.create_kyc_validation_transaction(
            user_id=user_id,
            api_name=UserLedgerTransactionType.KYC_DL.value,
            status="ERROR",
            provider_name=KYCProvider.INTERNAL.value,
            http_status_code=500
        )
        start_time = time.time()
        # Step 1: Check if the DL is already cached
        cached_details = self.__get_dl_kyc_details_from_db(dl_no)
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
            dl_verification_response = cached_details.kyc_provider_response

        else:
            # Step 2: If not cached, get from API
            dl_verification_response = self.__get_dl_kyc_details_from_api(
                dl_no, dob, transaction)

        if transaction.status in getattr(KYCServiceBillableStatus, UserLedgerTransactionType.KYC_DL.value):
            self.user_ledger_transaction_handler.deduct_credits(
                user_id, UserLedgerTransactionType.KYC_DL.value, f"{transaction.status}|{dl_no}")

        return dl_verification_response, transaction.http_status_code

    def __get_dl_kyc_details_from_db(self, dl_no: str) -> Optional[KYCValidationTransaction]:
        """
        Get DL details from database cache.

        Args:
            dl_no: DL number to verify.

        Returns:
            Optional[KYCValidationTransaction]: Cached DL details or None if not found
        """
        try:
            transaction = self.kyc_repository.get_kyc_validation_transaction(
                api_name=UserLedgerTransactionType.KYC_DL.value,
                identifier=dl_no,
                kyc_service_billable_status=KYCServiceBillableStatus.KYC_DL
            )
            if transaction and transaction.kyc_provider_response:
                logger.info(f"Cache hit for DL {dl_no}")
                return transaction
            return None
        except Exception as e:
            logger.error(f"Error fetching DL {dl_no} from cache: {str(e)}")
            return None

    def __get_dl_kyc_details_from_api(
        self, dl_no: str, dob: str, transaction: KYCValidationTransaction
    ) -> dict:
        """
        Get DL details from external API.

        Args:
            dl_no: DL number to verify
            dob: DOB to verify
            transaction: KYC validation transaction object

        Returns:
            dict: DL verification details from API
        """
        try:
            # Call external API
            response, tat = DLService.call_external_api(dl_no, dob)
            external_response = response.json()

            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=response.status_code,
                tat=tat,
                message=external_response.get("message", "No message provided"),
                kyc_transaction_details={"dl_no": dl_no, "dob": dob},
                kyc_provider_request={"dl_no": dl_no, "dob": dob},
                kyc_provider_response=external_response,
                status=self.__determine_status(response.status_code, external_response.get("status_code", 0)),
                is_cached=False,
                provider_name=KYCProvider.AITAN.value
            )
            return external_response

        except Exception as e:
            logger.error(f"Error fetching DL {dl_no} from API: {str(e)}")
            raise e

    def __determine_status(self, http_status_code: int, response_status_code: int) -> str:
        """
        Determine the status of the DL verification.

        Args:
            http_status_code: HTTP status code of the API response
            response_status_code: Status code of the API response

        Returns:
            str: Status of the DL verification
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
