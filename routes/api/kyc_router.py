# Standard library imports
from typing import Union

# Third-party library imports
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

# Local application imports
from dependencies.logger import logger

from dto.kyc_dto import PanVerificationRequest, VehicleVerificationRequest
from dto.common_dto import APISuccessResponse

from handlers.auth_handlers import AuthHandler
from handlers.pan_handler import PanHandler
from handlers.rc_handler import RCHandler

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
            message="PAN Verification Successful",
            result=pan_verification_response,
            http_status_code=http_status_code
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)})


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
    return await RCHandler.verify_vehicle(request, str(user.id))
