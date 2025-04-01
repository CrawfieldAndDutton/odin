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

from services.aitan_services import EmploymentLatestService


class EmploymentLatestHandler:

    def __init__(self):
        self.user_repository = UserRepository()
        self.kyc_repository = KYCRepository()
        self.user_ledger_transaction_handler = UserLedgerTransactionHandler()

    def get_employment_latest_details(
        self, uan: str, pan: str, mobile: str, dob: str,
        employer_name: str, employee_name: str, user_id: str
    ) -> Tuple[dict, int]:
        """
        Get Employment Latest details, first checking cache then API.

        Args:
            uan: UAN number to verify
            pan: PAN number to verify
            mobile: Mobile number to verify
            dob: Date of birth to verify
            employer_name: Employer name to verify
            employee_name: Employee name to verify
            user_id: ID of the user making the request

        Returns:
            dict: Employment Latest verification details
        """
        # Check if user has sufficient credits
        if self.user_repository.get_user_by_id(user_id).credits < ServicePricing.EV_EMPLOYMENT_LATEST_COST:
            logger.error(
                f"User {user_id} has insufficient credits to verify Employment Latest "
                f"{uan} {pan} {mobile} {dob} {employer_name} {employee_name}")
            raise InsufficientCreditsException()

        transaction = self.kyc_repository.create_kyc_validation_transaction(
            user_id=user_id,
            api_name=UserLedgerTransactionType.EV_EMPLOYMENT_LATEST.value,
            status="ERROR",
            provider_name=KYCProvider.INTERNAL.value,
            http_status_code=500
        )
        start_time = time.time()
        # Step 1: Check if the Employment Latest is already cached
        cached_details = self.__get_employment_latest_details_from_db(
            uan, pan, mobile, dob, employer_name, employee_name)
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
            employment_latest_verification_response = cached_details.kyc_provider_response

        else:
            # Step 2: If not cached, get from API
            employment_latest_verification_response = self.__get_employment_latest_details_from_api(
                uan, pan, mobile, dob, employer_name, employee_name, transaction)

        if transaction.status in getattr(
            KYCServiceBillableStatus,
            UserLedgerTransactionType.EV_EMPLOYMENT_LATEST.value
        ):
            self.user_ledger_transaction_handler.deduct_credits(
                user_id, UserLedgerTransactionType.EV_EMPLOYMENT_LATEST.value,
                f"{transaction.status}|{uan}")

        return employment_latest_verification_response, transaction.http_status_code

    def __get_employment_latest_details_from_db(
        self, uan: str, pan: str, mobile: str, dob: str,
        employer_name: str, employee_name: str
    ) -> Optional[KYCValidationTransaction]:
        """
        Get Employment Latest details from database cache.

        Args:
            uan: UAN number to verify

        Returns:
            Optional[KYCValidationTransaction]: Cached Employment Latest details or None if not found
        """
        try:
            transaction = self.kyc_repository.get_kyc_validation_transaction(
                api_name=UserLedgerTransactionType.EV_EMPLOYMENT_LATEST.value,
                identifier=uan or dob or pan or mobile or employer_name or employee_name,
                kyc_service_billable_status=KYCServiceBillableStatus.EV_EMPLOYMENT_LATEST
            )
            if transaction and transaction.kyc_provider_response:
                logger.info(
                    f"Cache hit for Employment Latest {uan} {pan} {mobile} {dob} {employer_name} {employee_name}")
                return transaction
            return None
        except Exception as e:
            logger.error(
                f"Error fetching Employment Latest "
                f"{uan} {pan} {mobile} {dob} {employer_name} {employee_name} from cache: {str(e)}")
            return None

    def __get_employment_latest_details_from_api(
        self, uan: str, pan: str, mobile: str, dob: str,
        employer_name: str, employee_name: str,
        transaction: KYCValidationTransaction
    ) -> dict:
        """
        Get Employment Latest details from external API.

        Args:
            uan: UAN number to verify
            transaction: KYC validation transaction object

        Returns:
            dict: Employment Latest verification details from API
        """
        try:
            # Call external API
            logger.info(
                f"Calling Employment Latest API for {uan} {pan} {mobile} {dob} {employer_name} {employee_name}")
            response, tat = EmploymentLatestService.call_external_api(
                uan, pan, mobile, dob, employer_name, employee_name)
            external_response = response.json()

            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=response.status_code,
                tat=tat,
                message=external_response.get("message", "No message provided"),
                kyc_transaction_details={"uan": uan, "pan": pan, "mobile": mobile, "dob": dob,
                                         "employer_name": employer_name, "employee_name": employee_name},
                kyc_provider_request={"uan": uan, "pan": pan, "mobile": mobile, "dob": dob,
                                      "employer_name": employer_name, "employee_name": employee_name},
                kyc_provider_response=external_response,
                status=self.__determine_status(response.status_code, external_response.get("status_code", 0)),
                is_cached=False,
                provider_name=KYCProvider.AITAN.value
            )
            return external_response

        except Exception as e:
            logger.error(
                f"Error fetching Employment Latest "
                f"{uan} {pan} {mobile} {dob} {employer_name} {employee_name} from API: {str(e)}")
            raise e

    def __determine_status(self, http_status_code: int, response_status_code: int) -> str:
        """
        Determine the status of the Employment Latest verification.

        Args:
            http_status_code: HTTP status code of the API response
            response_status_code: Status code of the API response

        Returns:
            str: Status of the Employment Latest verification
        """
        status = "ERROR"
        if http_status_code == 200:
            if response_status_code == 100:
                status = "FOUND"
            elif response_status_code == 101:
                status = "BAD_REQUEST"
            elif response_status_code == 102:
                status = "NOT_FOUND"
            else:
                status = "ERROR"
        elif http_status_code == 400:
            status = "BAD_REQUEST"

        return status
