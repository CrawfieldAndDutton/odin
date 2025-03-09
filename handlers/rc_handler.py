# Standard library imports
from datetime import datetime
from typing import Dict, Any, Optional, Union

# Third-party library imports
from fastapi.responses import JSONResponse
from fastapi import status

# Local application imports
from dependencies.constants import UserLedgerTransactionType
from dependencies.exceptions import InsufficientCreditsException
from dependencies.logger import logger

from dto.kyc_dto import VehicleVerificationRequest, APISuccessResponse

from handlers.user_ledger_transaction_handler import UserLedgerTransactionHandler

from models.kyc_model import KYCValidationTransaction

from repositories.kyc_repository import KYCRepository

from services.aitan_services import RCService


class RCHandler:

    def __init__(self, ledger_handler: UserLedgerTransactionHandler):
        self.ledger_handler = ledger_handler

    def verify_vehicle(
        self,
        request: VehicleVerificationRequest,
        user_id: str
    ) -> Union[APISuccessResponse, JSONResponse]:
        """
        Verify vehicle using registration number.

        Args:
            request: Vehicle verification request containing registration number
            user_id: ID of the user making the request

        Returns:
            VehicleVerificationResponse or JSONResponse
        """
        reg_no = request.reg_no
        start_time = datetime.now()

        logger.info(f"Starting vehicle verification for user {user_id} with registration number {reg_no}")

        # Check if user has sufficient credits
        if not self.ledger_handler.check_if_eligible(user_id, UserLedgerTransactionType.KYC_RC):
            logger.error(f"User {user_id} has insufficient credits to verify RC {reg_no}")
            raise InsufficientCreditsException()

        # Check for cached record
        cached_record = KYCRepository.get_cached_record_vehicle("RC_V1", {"reg_no": reg_no}, user_id)
        logger.info(f"Cache check result for reg_no {reg_no}: {'Hit' if cached_record else 'Miss'}")

        if cached_record:
            logger.info(f'Cache hit: Using INTERNAL data for reg_no {reg_no}')
            end_time = datetime.now()
            tat = (end_time - start_time).total_seconds()
            logger.info(f"Cache TAT: {tat} seconds")
            return RCHandler._handle_cached_record(cached_record, reg_no, user_id, tat)

        try:
            logger.info(f"Calling external API for reg_no {reg_no}")
            response, tat = RCService.call_external_api(reg_no)
            external_response = response.json()
            logger.info(f"External API response received with status code {response.status_code} in {tat} seconds")

            status = RCHandler._determine_status(response)
            logger.info(f"Determined status: {status}")

            transaction = RCHandler._create_transaction(
                response, tat, status, user_id,  {"reg_no": reg_no}, external_response, is_cached=True
            )
            logger.info(f"Created transaction: {transaction}")
            transaction.save()
            logger.info("Saved transaction to database")

            if status in ["FOUND", "NOT_FOUND"]:
                self.ledger_handler.deduct_credits(user_id, UserLedgerTransactionType.KYC_RC)

            if response.status_code == 206:
                logger.info(f"Returning partial JSONResponse with status code: {response.status_code}")
                partial_response = JSONResponse(
                    status_code=response.status_code,
                    content={
                        "http_status_code": response.status_code,
                        "message": "Success",
                        "error": external_response.get("message")}
                )
                logger.info(f"Error response content: {partial_response.body}")
                return partial_response
            if response.status_code != 200 and response.status_code != 206:
                logger.info(f"Returning error JSONResponse with status code: {response.status_code}")
                error_response = JSONResponse(
                    status_code=response.status_code,
                    content={
                        "http_status_code": response.status_code,
                        "message": "Failure",
                        "error": external_response.get("message")}
                )
                logger.info(f"Error response content: {error_response.body}")
                return error_response
            logger.info(f"Returning successful vehicle verification response for user {user_id}")
            success_response = APISuccessResponse(
                http_status_code=response.status_code,
                message="Success",
                result=external_response.get("result", {}),
            )
            logger.info(f"Success response: {success_response}")
            return success_response

        except Exception as e:
            logger.error(f"Exception occurred during vehicle verification: {str(e)}", exc_info=True)
            return RCHandler._handle_exception(e, reg_no, user_id)

    @staticmethod
    def _handle_cached_record(
        cached_record: Any,
        reg_no: str,
        user_id: str,
        tat: float
    ) -> Union[APISuccessResponse, JSONResponse]:
        """
        Handle cached vehicle record.

        Args:
            cached_record: Cached record from database
            reg_no: Vehicle registration number
            user_id: ID of the user making the request
            tat: Turn around time in seconds

        Returns:
            VehicleVerificationResponse or JSONResponse
        """
        logger.info(f"Handling cached record for reg_no {reg_no}")

        if cached_record.http_status_code == 200:
            status = "FOUND"
        elif cached_record.http_status_code == 206:
            status = "NOT_FOUND"
        elif cached_record.http_status_code == 400:
            status = "BAD_REQUEST"
        elif cached_record.http_status_code == 429:
            status = "TOO_MANY_REQUESTS"
        else:
            status = "ERROR"

        logger.info(f"Cached record status: {status}")

        transaction = KYCValidationTransaction(
            api_name=UserLedgerTransactionType.KYC_RC,
            provider_name="INTERNAL",
            is_cached=False,
            tat=tat,
            http_status_code=cached_record.http_status_code,
            status=status,
            message=cached_record.message,
            kyc_transaction_details={"reg_no": reg_no},
            kyc_provider_request=cached_record.kyc_provider_request,
            kyc_provider_response=cached_record.kyc_provider_response,
            user_id=user_id,
        )

        logger.info(f"Created cached transaction: {transaction}")
        transaction.save()
        logger.info("Saved cached transaction to database")
        if cached_record.http_status_code == 206:
            logger.info(f"Returning partial JSONResponse with status code: {cached_record.http_status_code}")
            partial_response = JSONResponse(
                status_code=cached_record.http_status_code,
                content={
                    "http_status_code": cached_record.http_status_code,
                    "message": "Success",
                    "error": cached_record.kyc_provider_response.get("message")
                }
            )
            logger.info(f"Error response content: {partial_response.body}")
            return partial_response
        if cached_record.http_status_code != 200 and cached_record.http_status_code != 206:
            logger.info(f"Returning cached error response with status code: {cached_record.http_status_code}")
            error_response = JSONResponse(
                status_code=cached_record.http_status_code,
                content={
                    "http_status_code": cached_record.http_status_code,
                    "message": "Failure",
                    "error": cached_record.message}
            )
            logger.info(f"Cached error response content: {error_response.body}")
            return error_response

        logger.info(f"Returning cached successful response for user {user_id}")
        success_response = APISuccessResponse(
            http_status_code=cached_record.http_status_code,
            message="Success",
            result=cached_record.kyc_provider_response.get("result", {}),
        )
        logger.info(f"Cached success response: {success_response}")
        return success_response

    @staticmethod
    def _determine_status(response: Any) -> str:
        """
        Determine status from response status code.

        Args:
            response: Response object with status_code attribute

        Returns:
            String representing the status
        """
        if response.status_code == 200:
            return "FOUND"
        elif response.status_code == 206:
            return "NOT_FOUND"
        elif response.status_code == 400:
            return "BAD_REQUEST"
        elif response.status_code == 429:
            return "TOO_MANY_REQUESTS"
        return "ERROR"

    @staticmethod
    def _create_transaction(
        response: Any,
        tat: float,
        status: str,
        user_id: str,
        payload: Optional[Dict[str, Any]] = None,
        external_response: Optional[Dict[str, Any]] = None,
        is_cached: bool = True
    ) -> KYCValidationTransaction:
        """
        Create KYC validation transaction.

        Args:
            response: Response object
            tat: Turn around time in seconds
            status: Transaction status
            user_id: ID of the user making the request
            payload: Request payload
            external_response: External API response
            is_cached: when the record is cached is True, otherwise False

        Returns:
            KYCValidationTransaction object
        """
        provider_name = "AITAN" if is_cached else "INTERNAL"
        logger.info(f"Creating transaction with provider {provider_name}, status {status}, TAT {tat}s")

        if payload is None:
            payload = {}

        transaction = KYCValidationTransaction(
            api_name=UserLedgerTransactionType.KYC_RC,
            provider_name=provider_name,
            is_cached=is_cached,
            tat=tat,
            http_status_code=response.status_code,
            status=status,
            message=external_response.get("message", "No message provided") if external_response else response.message,
            kyc_transaction_details={"reg_no": payload.get("reg_no", "")},
            kyc_provider_request=payload,
            kyc_provider_response=external_response,
            user_id=user_id,
        )

        logger.info(f"Transaction details: {transaction}")
        return transaction

    @staticmethod
    def _handle_exception(
        e: Exception,
        reg_no: str,
        user_id: str,
    ) -> JSONResponse:
        """
        Handle exceptions during vehicle verification.

        Args:
            e: Exception object
            reg_no: Vehicle registration number
            user_id: ID of the user making the request

        Returns:
            JSONResponse with error details
        """
        error_message = f"An unexpected error occurred: {str(e)}"
        logger.error(error_message, exc_info=True)

        transaction = KYCValidationTransaction(
            api_name=UserLedgerTransactionType.KYC_RC,
            provider_name="AITAN",
            is_cached=False,
            tat=0,
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            status="ERROR",
            message=error_message,
            kyc_transaction_details={"reg_no": reg_no},
            kyc_provider_request={"reg_no": reg_no},
            kyc_provider_response={},
            user_id=user_id,
        )

        logger.info(f"Created error transaction: {transaction}")
        transaction.save()
        logger.info("Saved error transaction to database")

        error_response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "http_status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failure",
                "error": error_message}
        )
        logger.info(f"Error response content: {error_response.body}")
        return error_response
