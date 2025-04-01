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

from services.aitan_services import RCService


class RCHandler:

    def __init__(self):
        self.user_repository = UserRepository()
        self.kyc_repository = KYCRepository()
        self.user_ledger_transaction_handler = UserLedgerTransactionHandler()

    def get_rc_kyc_details(self, reg_no: str, user_id: str) -> Tuple[dict, int]:
        """
        Get RC KYC details, first checking cache then API.

        Args:
            reg_no: registration number to verify
            user_id: ID of the user making the request

        Returns:
            dict: RC verification details
        """
        # Check if user has sufficient credits
        if self.user_repository.get_user_by_id(user_id).credits < ServicePricing.KYC_RC_COST:
            logger.error(f"User {user_id} has insufficient credits to verify RC {reg_no}")
            raise InsufficientCreditsException()

        transaction = self.kyc_repository.create_kyc_validation_transaction(
            user_id=user_id,
            api_name=UserLedgerTransactionType.KYC_RC.value,
            status="ERROR",
            provider_name=KYCProvider.INTERNAL.value,
            http_status_code=500
        )
        start_time = time.time()
        # Step 1: Check if the registration number is already cached
        cached_details = self.__get_rc_kyc_details_from_db(reg_no)
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
            rc_verification_response = cached_details.kyc_provider_response

        else:
            # Step 2: If not cached, get from API
            rc_verification_response = self.__get_rc_kyc_details_from_api(reg_no, transaction)

        if transaction.status in getattr(KYCServiceBillableStatus, UserLedgerTransactionType.KYC_RC.value):
            self.user_ledger_transaction_handler.deduct_credits(
                user_id, UserLedgerTransactionType.KYC_RC.value, f"{transaction.status}|{reg_no}")

        return rc_verification_response, transaction.http_status_code

    def __get_rc_kyc_details_from_db(self, reg_no: str) -> Optional[KYCValidationTransaction]:
        """
        Get RC details from database cache.

        Args:
            reg_no: registration number to verify

        Returns:
            Optional[KYCValidationTransaction]: Cached RC details or None if not found
        """
        try:
            transaction = self.kyc_repository.get_kyc_validation_transaction(
                api_name=UserLedgerTransactionType.KYC_RC.value,
                identifier=reg_no,
                kyc_service_billable_status=KYCServiceBillableStatus.KYC_RC
            )
            if transaction and transaction.kyc_provider_response:
                logger.info(f"Cache hit for RC {reg_no}")
                return transaction
            return None
        except Exception as e:
            logger.error(f"Error fetching reg_no {reg_no} from cache: {str(e)}")
            return None

    def __get_rc_kyc_details_from_api(self, reg_no: str, transaction: KYCValidationTransaction) -> dict:
        """
        Get RC details from external API.

        Args:
            reg_no: registration number to verify
            transaction: KYC validation transaction object

        Returns:
            dict: reg_no verification details from API
        """
        try:
            # Call external API
            logger.info(f"Calling RC API for {reg_no}")
            response, tat = RCService.call_external_api(reg_no)
            external_response = response.json()

            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=response.status_code,
                tat=tat,
                message=external_response.get("message", "No message provided"),
                kyc_transaction_details={"reg_no": reg_no},
                kyc_provider_request={"reg_no": reg_no},
                kyc_provider_response=external_response,
                status=self.__determine_status(response.status_code),
                is_cached=False,
                provider_name=KYCProvider.AITAN.value
            )
            return external_response

        except Exception as e:
            logger.error(f"Error fetching RC {reg_no} from API: {str(e)}")
            raise e

    def __determine_status(self, http_status_code: int) -> str:
        """
        Determine the status of the RC verification.

        Args:
            http_status_code: HTTP status code of the API response

        Returns:
            str: Status of the RC verification
        """
        status = "ERROR"
        if http_status_code == 200:
            return "FOUND"
        elif http_status_code == 206:
            return "NOT_FOUND"
        elif http_status_code == 400:
            return "BAD_REQUEST"
        elif http_status_code == 429:
            return "TOO_MANY_REQUESTS"

        return status
