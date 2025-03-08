# Standard library imports
from typing import Union

# Third-party library imports
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

# Local application imports
from dto.kyc_dto import PanVerificationRequest, APISuccessResponse, VehicleVerificationRequest

from handlers.auth_handlers import AuthHandler
from handlers.pan_handler import PanHandler
from handlers.rc_handler import RCHandler

from models.user_model import User as UserModel

kyc_router = APIRouter(prefix="/dashboard/api/v1", tags=["KYC Verification API"])


@kyc_router.post("/pan/verify", response_model=APISuccessResponse)
async def verify_pan(
    request: PanVerificationRequest,
    user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> Union[APISuccessResponse, JSONResponse]:
    """
    Verify PAN details.

    Args:
        request: PAN verification request
        fastapi_request: FastAPI request object
        user: Authenticated user

    Returns:
        PanVerificationResponse or JSONResponse for error cases
    """
    return await PanHandler.verify_pan(request, str(user.id))


@kyc_router.post("/rc/verify", response_model=APISuccessResponse)
async def verify_vehicle(
    request: VehicleVerificationRequest,
    user: UserModel = Depends(AuthHandler.get_current_active_user)
) -> Union[APISuccessResponse, JSONResponse]:
    """
    Verify vehicle registration details.

    Args:
        request: Vehicle verification request
        fastapi_request: FastAPI request object
        user: Authenticated user

    Returns:
        VehicleVerificationResponse or JSONResponse for error cases
    """
    return await RCHandler.verify_vehicle(request, str(user.id))
