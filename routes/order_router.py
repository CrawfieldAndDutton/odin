from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from dto.order_dto import PanVerificationRequest, PanVerificationResponse
from dto.order_dto import VehicleVerificationRequest, VehicleVerificationResponse
from services.order_service import PanService, VehicleService
from dependencies.dependency import get_current_active_user
from models.user_model import User as UserModel
import logging
import re
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


logger = logging.getLogger(__name__)
pan_router = APIRouter(prefix="/api/pan", tags=["Pan Verification API"])

vehicle_router = APIRouter(prefix="/api/vehicle",
                           tags=["Vehicle Verification API"])


@pan_router.post("/verify-pan", response_model=PanVerificationResponse)
async def verify_pan(
    request_body: PanVerificationRequest,
    request: Request,
    user_agent: Optional[str] = Header(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    pan_pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    if not re.match(pan_pattern, request_body.pan.upper()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid Input Parameter - 400")
    """
    Verify vehicle details using the registration number.
    """
    client_info = {
        "ip": request.client.host,
        "user_agent": user_agent,
        "user_id": str(current_user.id)
    }

    service = PanService()
    result = service.verify_pan(request_body.pan, client_info)

    if not isinstance(result, dict):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Invalid response format from service")

    status_code = result.get("status_code")

    status_code_mapping = {
        100: (status.HTTP_200_OK, "Active PAN"),
        101: (status.HTTP_400_BAD_REQUEST, "Inactive PAN - Status Code : 101"),
        102: (status.HTTP_403_FORBIDDEN, "Invalid PAN - Status Code : 102"),
        400: (status.HTTP_400_BAD_REQUEST, "Invalid Input Parameter - Status Code : 400"),
        429: (status.HTTP_429_TOO_MANY_REQUESTS, "Rate Limited - Status Code : 429"),
        500: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error"),
        503: (status.HTTP_503_SERVICE_UNAVAILABLE, "Source Down"),
        504: (status.HTTP_504_GATEWAY_TIMEOUT, "Gateway Timeout"),
        502: (status.HTTP_502_BAD_GATEWAY, "Bad Gateway")
    }

    if status_code in status_code_mapping:
        http_code, description = status_code_mapping[status_code]
        if http_code != status.HTTP_200_OK:
            raise HTTPException(status_code=http_code, detail=description)
        return result

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected Error")


@vehicle_router.post("/verify-vehicle", response_model=VehicleVerificationResponse)
async def verify_vehicle(
    request_body: VehicleVerificationRequest,
    request: Request,
    user_agent: Optional[str] = Header(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Verify vehicle details using the registration number.
    """
    try:
        client_info = {
            "ip": request.client.host,
            "user_agent": user_agent,
            "user_id": str(current_user.id)
        }

        service = VehicleService()
        result = service.verify_vehicle(request_body.reg_no, client_info)

        # Debug log to see what's coming back from the service
        logger.debug(f"Service response: {result}")

        if result.get("status") == "error":
            error_message = result.get("message", "Unknown error")

            # Log the error details for debugging
            logger.info(f"Error response received: {result}")

            # Check if registration number is valid but not found
            # Adjust these conditions based on what your service actually returns
            if (
                "not found" in error_message.lower() or
                "no record" in error_message.lower() or
                "no data" in error_message.lower() or
                "not in database" in error_message.lower() or
                # If your service uses error codes
                result.get("error_code") == "NOT_FOUND"
            ):
                logger.info(
                    f"Returning 206 Not Found for reg_no: {request_body.reg_no}")
                # Return 206 for correctly formatted reg_no that doesn't exist
                raise HTTPException(
                    status_code=206,  # Using 206 as specified
                    detail={
                        "status": "not_found",
                        "reg_no": request_body.reg_no,
                        "message": f"Registration number not found: {error_message}"
                    }
                )
            else:
                logger.info(
                    f"Returning 400 Bad Request for reg_no: {request_body.reg_no}")
                # Return 400 Bad Request for other client errors
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "reg_no": request_body.reg_no,
                        "message": error_message
                    }
                )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions to maintain their status codes
        raise
    except Exception as e:
        # Log the unexpected error
        logger.error(f"Internal server error: {str(e)}")
        # Return 500 Internal Server Error for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "An unexpected error occurred"
            }
        )
