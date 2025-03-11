# Standard library imports
from typing import Union
import json

# Third-party library imports
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

# Local application imports
from dependencies.logger import logger
from dependencies.exceptions import InsufficientCreditsException

from dto.kyc_dto import PanVerificationRequest, VehicleVerificationRequest
from dto.kyc_dto import VoterVerificationRequest, DLVerificationRequest, PassportVerificationRequest
from dto.common_dto import APISuccessResponse

from handlers.auth_handlers import AuthHandler
from handlers.pan_handler import PanHandler
from handlers.rc_handler import RCHandler
from handlers.voter_handler import VoterHandler
from handlers.dl_handler import DLHandler
from handlers.passport_handler import PassportHandler
from models.user_model import User as UserModel

kyc_router = APIRouter(prefix="/api/v1", tags=["KYC Verification API"])


@kyc_router.post("/pan/verify", response_model=APISuccessResponse)
def verify_pan(
    request: PanVerificationRequest,
    user: UserModel = Depends(AuthHandler.get_api_client)
) -> Union[APISuccessResponse, JSONResponse]:
    """
    Verify PAN details.

    Args:
        request: PAN verification request
        user: Authenticated user associated with the API client

    Returns:
        PanVerificationResponse or JSONResponse for error cases
    """
    try:
        pan_verification_response, http_status_code = PanHandler().get_pan_kyc_details(
            pan=request.pan, user_id=str(user.id)
        )
        logger.info(f"PAN Verification Response: {pan_verification_response}")

        if http_status_code != status.HTTP_200_OK:
            return JSONResponse(
                status_code=http_status_code,
                content={
                    "http_status_code": http_status_code,
                    "message": "Failure",
                    "error": pan_verification_response.get('message')
                }
            )

        return APISuccessResponse(
            http_status_code=http_status_code,
            message="PAN Verification Successful",
            result=pan_verification_response,
        )
    except InsufficientCreditsException as e:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={"message": str(e.detail)}
        )
    except Exception as e:
        logger.error(f"Error in verify_pan: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )


@kyc_router.post("/rc/verify", response_model=APISuccessResponse)
async def verify_vehicle(
    request: VehicleVerificationRequest,
    user: UserModel = Depends(AuthHandler.get_api_client)
) -> Union[APISuccessResponse, JSONResponse]:
    """
    Verify vehicle registration details.

    Args:
        request: Vehicle verification request
        user: Authenticated user associated with the API client

    Returns:
        VehicleVerificationResponse or JSONResponse for error cases
    """
    try:
        rc_verification_response, http_status_code = RCHandler().get_rc_kyc_details(
            reg_no=request.reg_no, user_id=str(user.id)
        )
        logger.info(f"RC Verification Response: {rc_verification_response}")

        if http_status_code != status.HTTP_200_OK:
            return JSONResponse(
                status_code=http_status_code,
                content={
                    "http_status_code": http_status_code,
                    "message": "Failure",
                    "error": rc_verification_response.get('message')
                }
            )

        return APISuccessResponse(
            message="RC Verification Successful",
            result=rc_verification_response,
            http_status_code=http_status_code
        )
    except InsufficientCreditsException as e:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={"message": str(e.detail)}
        )
    except Exception as e:
        logger.error(f"Error in verify_vehicle: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )
    # return await RCHandler.verify_vehicle(request, str(user.id))


@kyc_router.post("/voter/verify", response_model=APISuccessResponse)
def verify_voter(
    request: VoterVerificationRequest,
    user: UserModel = Depends(AuthHandler.get_api_client)
) -> Union[APISuccessResponse, JSONResponse]:
    """
    Verify voter details.

    Args:
        request: Voter verification request
        user: Authenticated user associated with the API client

    Returns:
        VehicleVerificationResponse or JSONResponse for error cases
    """
    try:
        voter_verification_response, http_status_code = VoterHandler().get_voter_kyc_details(
            epic_no=request.epic_no, user_id=str(user.id)
        )
        logger.info(f"VOTER Verification Response: {voter_verification_response}")

        if http_status_code != status.HTTP_200_OK:
            return JSONResponse(
                status_code=http_status_code,
                content={
                    "http_status_code": http_status_code,
                    "message": "Failure",
                    "error": voter_verification_response.get('message')
                }
            )

        return APISuccessResponse(
            http_status_code=http_status_code,
            message="VOTER Verification Successful",
            result=voter_verification_response,
        )
    except InsufficientCreditsException as e:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={"message": str(e.detail)}
        )
    except Exception as e:
        logger.error(f"Error in verify_voter: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )


@kyc_router.post("/dl/verify", response_model=APISuccessResponse)
def verify_dl(
    request: DLVerificationRequest,
    user: UserModel = Depends(AuthHandler.get_api_client)
) -> Union[APISuccessResponse, JSONResponse]:
    """
    Verify DL details.

    Args:
        request: DL verification request
        user: Authenticated user associated with the API client
        Returns:
            DLVerificationResponse or JSONResponse for error cases
        """
    try:
        dl_verification_response, http_status_code = DLHandler().get_dl_kyc_details(
            dl_no=request.dl_no,
            dob=request.dob,
            user_id=str(user.id)
        )
        dl_verification_response = json.loads(json.dumps(dl_verification_response))
        logger.info(f"DL Verification Response: {dl_verification_response}")

        if http_status_code != status.HTTP_200_OK:
            return JSONResponse(
                status_code=http_status_code,
                content={
                    "http_status_code": http_status_code,
                    "message": "Failure",
                    "error": dl_verification_response.get('message')
                }
            )
        return APISuccessResponse(
            http_status_code=http_status_code,
            message="DL Verification Successful",
            result=dl_verification_response,
        )
    except InsufficientCreditsException as e:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={"message": str(e.detail)}
        )
    except Exception as e:
        logger.error(f"Error in verify_passport: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )


@kyc_router.post("/passport/verify", response_model=APISuccessResponse)
def verify_passport(
    request: PassportVerificationRequest,
    user: UserModel = Depends(AuthHandler.get_api_client)
) -> Union[APISuccessResponse, JSONResponse]:
    """
    Verify passport details.

    Args:
        request: Passport verification request
        user: Authenticated user associated with the API client

    Returns:
        PassportVerificationResponse or JSONResponse for error cases
    """
    try:
        passport_verification_response, http_status_code = PassportHandler().get_passport_kyc_details(
            file_number=request.file_number,
            dob=request.dob,
            name=request.name,
            user_id=str(user.id)
        )
        logger.info(f"PASSPORT Verification Response: {passport_verification_response}")

        if http_status_code != status.HTTP_200_OK:
            return JSONResponse(
                status_code=http_status_code,
                content={
                    "http_status_code": http_status_code,
                    "message": "Failure",
                    "error": passport_verification_response.get('message')
                }
            )

        return APISuccessResponse(
            http_status_code=http_status_code,
            message="PASSPORT Verification Successful",
            result=passport_verification_response,
        )
    except InsufficientCreditsException as e:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={"message": str(e.detail)}
        )
    except Exception as e:
        logger.error(f"Error in verify_passport: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )
