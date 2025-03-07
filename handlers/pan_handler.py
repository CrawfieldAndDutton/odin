# Standard library imports
from datetime import datetime
from typing import Optional, Dict, Any

# Third-party library imports
from fastapi import Request
from fastapi.responses import JSONResponse

# Local application imports
from dependencies.logger import logger
from models.kyc_model import KYCValidationTransaction
from dto.kyc_dto import PanVerificationRequest, APISuccessResponse
from repositories.kyc_repository import KYCRepository
from services.aitan_services import PanService


class PanHandler:
    @staticmethod
    async def verify_pan(
        request: PanVerificationRequest,
        fastapi_request: Request,
        user_id: str
    ) -> JSONResponse | APISuccessResponse:
        pan = request.pan
        start_time = datetime.now()

        logger.info(f"Starting PAN verification for user {user_id} with PAN {pan}")

        cached_record = KYCRepository.get_cached_record_pan("PAN", {"pan": pan}, user_id)

        end_time = datetime.now()
        if cached_record:
            tat = (end_time - start_time).total_seconds()
            logger.info(f"Cached record found for PAN {pan}. Handling cached record.")
            return PanHandler._handle_cached_record(cached_record, pan, user_id, fastapi_request, tat)

        try:
            logger.info(f"No cached record found for PAN {pan}. Calling external API.")
            response, tat = await PanService.call_external_api(pan, fastapi_request, user_id)
            external_response = response.json()
            status = PanHandler._determine_status(response, external_response)
            transaction = PanHandler._create_transaction(
                response, tat, status, user_id, fastapi_request,
                payload={"pan": pan}, external_response=external_response,
                is_cached=False
            )
            logger.info(f"Transaction to be saved: {transaction}")
            transaction.save()
            logger.info(f"Transaction saved successfully for PAN {pan}.")

            if response.status_code != 200:
                logger.exception(f"Returning JSONResponse with status code: {response.status_code}")
                return JSONResponse(
                    status_code=response.status_code,
                    content={
                        "http_status_code": response.status_code,
                        "message": "Failure",
                        "error": external_response.get("message")}
                )

            logger.info(f"Returning successful PAN verification response for user {user_id}")
            return APISuccessResponse(
                http_status_code=response.status_code,
                message="Success",
                result=external_response,
            )

        except Exception as e:
            logger.exception(f"Returning JSONResponse with status code: {500}")
            return PanHandler._handle_exception(e, pan, user_id, fastapi_request)

    @staticmethod
    def _handle_cached_record(
        cached_record: KYCValidationTransaction,
        pan: str,
        user_id: str,
        fastapi_request: Request,
        tat: float
    ) -> JSONResponse | APISuccessResponse:
        if cached_record.http_status_code == 200:
            if cached_record.kyc_provider_response.get("status_code") == 100:
                status = "FOUND"
            elif cached_record.kyc_provider_response.get("status_code") == 101:
                status = "FOUND"
            elif cached_record.kyc_provider_response.get("status_code") == 102:
                status = "NOT_FOUND"
            else:
                status = "ERROR"
        elif cached_record.http_status_code == 400:
            status = "BAD_REQUEST"
        else:
            status = "ERROR"
        transaction = KYCValidationTransaction(
            api_name="PAN",
            provider_name="INTERNAL",
            is_cached=True,
            tat=tat,
            message=cached_record.message,
            http_status_code=cached_record.http_status_code,
            status=status,
            kyc_transaction_details={"pan": pan},
            kyc_provider_request=cached_record.kyc_provider_request,
            kyc_provider_response=cached_record.kyc_provider_response,
            kyc_validation_transactions_logs={
                "ip": fastapi_request.client.host,
                "user_agent": fastapi_request.headers.get("user-agent"),
                "user_id": user_id,
            },
            user_id=user_id,
        )
        logger.info(f"Transaction to be saved (cached): {transaction}")
        transaction.save()
        logger.info(f"Transaction saved successfully for PAN {pan} (cached).")
        if cached_record.http_status_code != 200:
            logger.exception(f"Returning JSONResponse with status code: {cached_record.http_status_code}")
            return JSONResponse(
                status_code=cached_record.http_status_code,
                content={
                    "http_status_code": cached_record.http_status_code,
                    "message": "Failure",
                    "error": cached_record.message}
            )
        logger.info(f"Returning cached PAN verification result for user {user_id}")
        return APISuccessResponse(
            http_status_code=cached_record.http_status_code,
            message="Success",
            result=cached_record.kyc_provider_response,
        )

    @staticmethod
    def _determine_status(
        response: Any,
        external_response: Optional[Dict[str, Any]] = None
    ) -> str:
        if external_response:
            if external_response.get("status_code") in [100, 101]:
                return "FOUND"
            elif external_response.get("status_code") == 102:
                return "NOT_FOUND"
        if response.status_code == 200:
            return "FOUND"
        elif response.status_code == 400:
            return "BAD_REQUEST"
        return "ERROR"

    @staticmethod
    def _create_transaction(
        response: Any,
        tat: float,
        status: str,
        user_id: str,
        fastapi_request: Request,
        payload: Optional[Dict[str, Any]] = None,
        external_response: Optional[Dict[str, Any]] = None,
        is_cached: bool = True
    ) -> KYCValidationTransaction:
        provider_name = "INTERNAL" if is_cached else "AITAN"
        transaction = KYCValidationTransaction(
            api_name="PAN",
            provider_name=provider_name,
            is_cached=is_cached,
            tat=tat,
            http_status_code=response.status_code,
            status=status,
            message=external_response.get("message", "No message provided") if external_response else response.message,
            kyc_transaction_details={"pan": response.pan if not external_response else payload["pan"]},
            kyc_provider_request=payload if payload else response.kyc_provider_request,
            kyc_provider_response=external_response if external_response else response.kyc_provider_response,
            kyc_validation_transactions_logs={
                "ip": fastapi_request.client.host,
                "user_agent": fastapi_request.headers.get("user-agent"),
                "user_id": user_id,
            },
            user_id=user_id,
        )
        logger.info(f"Transaction created: {transaction}")
        return transaction

    @staticmethod
    def _handle_exception(
        e: Exception,
        pan: str,
        user_id: str,
        fastapi_request: Request
    ) -> JSONResponse:
        error_message = f"An unexpected error occurred: {str(e)}"
        logger.exception(error_message)
        transaction = KYCValidationTransaction(
            api_name="PAN",
            provider_name="AITAN",
            is_cached=False,
            tat=0,
            http_status_code=500,
            status="ERROR",
            message=error_message,
            kyc_transaction_details={"pan": pan},
            kyc_provider_request={"pan": pan},
            kyc_provider_response={},
            kyc_validation_transactions_logs={
                "ip": fastapi_request.client.host,
                "user_agent": fastapi_request.headers.get("user-agent"),
                "user_id": user_id,
            },
            user_id=user_id,
        )
        logger.info(f"Transaction to be saved (exception): {transaction}")
        transaction.save()
        logger.info(f"Transaction saved successfully for PAN {pan} (exception).")
        return JSONResponse(
            status_code=500,
            content={
                "http_status_code": 500,
                "message": "Failure",
                "error": error_message}
        )
