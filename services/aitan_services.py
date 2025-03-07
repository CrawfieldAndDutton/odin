# Standard library imports
from datetime import datetime
from typing import Dict, Any, Tuple

# Third-party library imports
import requests
from fastapi import Request
from requests.models import Response

# Local application imports
from dependencies.constants import VEHICLE_HEADERS, VEHICLE_PAYLOAD, PAN_HEADERS, PAN_PAYLOAD
from dependencies.config import Config
from dependencies.logger import logger


def calculate_tat(start_time: datetime, end_time: datetime) -> float:
    """Calculate turnaround time in seconds."""
    return (end_time - start_time).total_seconds()


def call_external_api(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Tuple[Response, float]:
    """
    Generic function to call an external API and calculate turnaround time.

    Args:
        url: The API URL to call.
        headers: The headers to include in the request.
        payload: The payload to send in the request.

    Returns:
        Tuple containing:
            - Response object
            - Turn around time in seconds
    """
    start_time = datetime.now()
    logger.info(f"Calling external API: {url}")
    response = requests.post(url, json=payload, headers=headers)
    end_time = datetime.now()
    tat = calculate_tat(start_time, end_time)
    return response, tat


class PanService:
    @staticmethod
    async def call_external_api(
        pan: str,
        fastapi_request: Request,
        user_id: str
    ) -> Tuple[Response, float]:
        """
        Call external API for PAN verification.

        Args:
            pan: PAN number to verify
            fastapi_request: FastAPI request object
            user_id: ID of the user making the request

        Returns:
            Tuple containing:
                - Response object
                - Turn around time in seconds
        """
        payload = {**PAN_PAYLOAD, "pan": pan}
        return call_external_api(Config.EXTERNAL_API_URL_PAN, PAN_HEADERS, payload)


class RCService:
    @staticmethod
    async def call_external_api(
        reg_no: str,
        fastapi_request: Request,
        user_id: str
    ) -> Tuple[Response, float]:
        """
        Call external API for vehicle registration verification.

        Args:
            reg_no: Vehicle registration number to verify
            fastapi_request: FastAPI request object
            user_id: ID of the user making the request

        Returns:
            Tuple containing:
                - Response object
                - Turn around time in seconds
        """
        payload = {**VEHICLE_PAYLOAD, "reg_no": reg_no}
        return call_external_api(Config.EXTERNAL_API_URL_VEHICLE, VEHICLE_HEADERS, payload)
