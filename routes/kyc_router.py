from fastapi import APIRouter, Depends, Request
from typing import Union
from fastapi.responses import JSONResponse
from models.user_model import User as UserModel
from dto.kyc_dto import PanVerificationRequest, PanVerificationResponse
from dto.kyc_dto import VehicleVerificationRequest, VehicleVerificationResponse
from handlers.auth_handlers import get_current_active_user
from handlers.pan_handler import PanHandler
from handlers.rc_handler import RCHandler

pan_router = APIRouter(prefix="/api/v1", tags=["PAN Verification API"])
vehicle_router = APIRouter(prefix="/api/v1", tags=["RC Verification API"])


@pan_router.post("/pan/verify", response_model=PanVerificationResponse)
async def verify_pan(
    request: PanVerificationRequest,
    fastapi_request: Request,
    user: UserModel = Depends(get_current_active_user)
) -> Union[PanVerificationResponse, JSONResponse]:
    """
    Verify PAN details.

    Args:
        request: PAN verification request
        fastapi_request: FastAPI request object
        user: Authenticated user

    Returns:
        PanVerificationResponse or JSONResponse for error cases
    """
    return await PanHandler.verify_pan(request, fastapi_request, str(user.id))


@vehicle_router.post("/rc/verify", response_model=VehicleVerificationResponse)
async def verify_vehicle(
    request: VehicleVerificationRequest,
    fastapi_request: Request,
    user: UserModel = Depends(get_current_active_user)
) -> Union[VehicleVerificationResponse, JSONResponse]:
    """
    Verify vehicle registration details.

    Args:
        request: Vehicle verification request
        fastapi_request: FastAPI request object
        user: Authenticated user

    Returns:
        VehicleVerificationResponse or JSONResponse for error cases
    """
    return await RCHandler.verify_vehicle(request, fastapi_request, str(user.id))
