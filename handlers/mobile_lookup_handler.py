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

from services.aitan_services import MobileLookupService


class MobileLookupHandler:

    def __init__(self):
        self.user_repository = UserRepository()
        self.kyc_repository = KYCRepository()
        self.user_ledger_transaction_handler = UserLedgerTransactionHandler()

    def get_mobile_lookup_kyc_details(self, mobile: str, user_id: str) -> Tuple[dict, int]:
        """
        Get Mobile Lookup details, first checking cache then API.

        Args:
            mobile: mobile number to verify
            user_id: ID of the user making the request

        Returns:
            dict: Mobile Lookup verification details
        """
        # Check if user has sufficient credits
        if self.user_repository.get_user_by_id(user_id).credits < ServicePricing.KYC_MOBILE_LOOKUP_COST:
            logger.error(f"User {user_id} has insufficient credits to verify mobile {mobile}")
            raise InsufficientCreditsException()

        transaction = self.kyc_repository.create_kyc_validation_transaction(
            user_id=user_id,
            api_name=UserLedgerTransactionType.KYC_MOBILE_LOOKUP.value,
            status="ERROR",
            provider_name=KYCProvider.INTERNAL.value,
            http_status_code=500
        )
        start_time = time.time()
        # Step 1: Check if the registration number is already cached
        cached_details = self.__get_mobile_lookup_details_from_db(mobile)
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
                provider_name=KYCProvider.INTERNAL.value,
            )
            mobile_lookup_verification_response = cached_details.kyc_provider_response

        else:
            # Step 2: If not cached, get from API
            mobile_lookup_verification_response = self.__get_mobile_lookup_details_from_api(mobile, transaction)

        if transaction.status in getattr(KYCServiceBillableStatus, UserLedgerTransactionType.KYC_MOBILE_LOOKUP.value):
            self.user_ledger_transaction_handler.deduct_credits(
                user_id, UserLedgerTransactionType.KYC_MOBILE_LOOKUP.value, f"{transaction.status}|{mobile}")

        return mobile_lookup_verification_response, transaction.http_status_code

    def __get_mobile_lookup_details_from_db(self, mobile: str) -> Optional[KYCValidationTransaction]:
        """
        Get Mobile Lookup details from database cache.

        Args:
            mobile: mobile number to verify

        Returns:
            Optional[KYCValidationTransaction]: Cached Mobile Lookup details or None if not found
        """
        try:
            transaction = self.kyc_repository.get_kyc_validation_transaction(
                api_name=UserLedgerTransactionType.KYC_MOBILE_LOOKUP.value,
                identifier=mobile,
                kyc_service_billable_status=KYCServiceBillableStatus.KYC_MOBILE_LOOKUP
            )
            if transaction and transaction.kyc_provider_response:
                logger.info(f"Cache hit for Mobile Lookup {mobile}")
                return transaction
            return None
        except Exception as e:
            logger.error(f"Error fetching mobile {mobile} from cache: {str(e)}")
            return None

    def __get_mobile_lookup_details_from_api(self, mobile: str, transaction: KYCValidationTransaction) -> dict:
        """
        Get Mobile Lookup details from external API.

        Args:
            mobile: mobile number to verify
            transaction: KYC validation transaction object

        Returns:
            dict: mobile verification details from API
        """
        try:
            # Call external API
            logger.info(f"Calling Mobile Lookup API for {mobile}")
            response, tat = MobileLookupService.call_external_api(mobile)
            external_response = response.json()

            # Calculate confidence scores
            confidence_scores = self.__determine_total_mobile_confidence_score(external_response, response.status_code)
            if response.status_code == 200:
                external_response["result"]["confidence_scores"] = confidence_scores
            # Update transaction with response details
            self.kyc_repository.update_kyc_validation_transaction(
                transaction,
                http_status_code=response.status_code,
                tat=tat,
                message=external_response.get("message", "No message provided"),
                kyc_transaction_details={"mobile": mobile},
                kyc_provider_request={"mobile": mobile},
                kyc_provider_response=external_response,
                status=self.__determine_status(response.status_code),
                is_cached=False,
                provider_name=KYCProvider.AITAN.value,
            )

            return external_response

        except Exception as e:
            logger.error(f"Error fetching Mobile Lookup {mobile} from API: {str(e)}")
            raise e

    def __determine_status(self, http_status_code: int) -> str:
        """
        Determine the status of the Mobile Lookup verification.

        Args:
            http_status_code: HTTP status code of the API response

        Returns:
            str: Status of the Mobile Lookup verification
        """
        status = "ERROR"
        if http_status_code == 200:
            return "FOUND"
        elif http_status_code == 206:
            return "PARTIAL_CONTENT"
        elif http_status_code == 400:
            return "BAD_REQUEST"
        elif http_status_code == 429:
            return "TOO_MANY_REQUESTS"
        elif http_status_code == 503:
            return "SOURCE_DOWN"
        return status

    def __calculate_social_media_score(self, result: dict) -> float:
        """
        Calculate social media confidence score.

        Args:
            result: result from Mobile Lookup API

        Returns:
            float: social media confidence score
        """
        score = 0.0
        if isinstance(result.get("whatsapp", {}), dict) and result["whatsapp"].get("registered"):
            score += 0.4
        if isinstance(result.get("instagram", {}), dict) and result["instagram"].get("registered"):
            score += 0.3
        if isinstance(result.get("facebook", {}), dict) and result["facebook"].get("registered"):
            score += 0.2
        if isinstance(result.get("twitter", {}), dict) and result["twitter"].get("registered"):
            score += 0.1
        return score

    def __calculate_ecommerce_score(self, result: dict) -> float:
        """
        Calculate ecommerce confidence score.

        Args:
            result: result from Mobile Lookup API

        Returns:
            float: ecommerce confidence score
        """
        score = 0.0
        if isinstance(result.get("amazon", {}), dict) and result["amazon"].get("registered"):
            score += 0.6
        if isinstance(result.get("flipkart", {}), dict) and result["flipkart"].get("registered"):
            score += 0.4
        return score

    def __calculate_payment_score(self, result: dict) -> float:
        """
        Calculate payment confidence score.

        Args:
            result: result from Mobile Lookup API

        Returns:
            float: payment confidence score
        """
        if isinstance(result.get("paytm", {}), dict) and result["paytm"].get("registered"):
            return 1.0
        return 0.0

    def __determine_total_mobile_confidence_score(self, mobile_lookup_response: dict, http_status_code: int) -> dict:
        """
        Determine the total mobile confidence score based on:
        - Social Media Score = Whatsapp (4/10) + Instagram (3/10) + Facebook (2/10) + Twitter (1/10)
        - Ecommerce Score = Amazon (3/5) + Flipkart (2/5)
        - Payment Score = Paytm (1/1)
        Total Score = (Social Media Score + Ecommerce Score + Payment Score) / 3

        Args:
            mobile_lookup_response: result from Mobile Lookup API

        Returns:
            dict: total mobile confidence score
        """

        if http_status_code == 200:
            result = mobile_lookup_response.get("result", {})
            if not isinstance(result, dict):
                logger.error(f"Invalid mobile lookup response format. Result is not a dictionary: {result}")
                return {
                    "social_media_score": 0.0,
                    "ecommerce_score": 0.0,
                    "payment_score": 0.0,
                    "confidence_score": 0.0
                }

            social_media_score = self.__calculate_social_media_score(result)
            ecommerce_score = self.__calculate_ecommerce_score(result)
            payment_score = self.__calculate_payment_score(result)

            total_score = ((social_media_score + ecommerce_score + payment_score) / 3)
            logger.info(
                f"Mobile confidence scores - Social Media: {social_media_score}, "
                f"Ecommerce: {ecommerce_score}, Payment: {payment_score}, "
                f"Total: {total_score}"
            )

            return {
                "social_media_score": round(social_media_score*100, 2),
                "ecommerce_score": round(ecommerce_score*100, 2),
                "payment_score": round(payment_score*100, 2),
                "confidence_score": round(total_score*100, 2)
            }
        else:
            return {
                "social_media_score": 0.0,
                "ecommerce_score": 0.0,
                "payment_score": 0.0,
                "confidence_score": 0.0
            }
