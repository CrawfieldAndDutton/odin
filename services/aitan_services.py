import requests
from typing import Dict, Any, Tuple
from datetime import datetime
from fastapi import Request
from requests.models import Response
from dependencies.constants import VEHICLE_HEADERS, VEHICLE_PAYLOAD
from dependencies.config import Config
from dependencies.constants import PAN_HEADERS, PAN_PAYLOAD
from dependencies.logger import logger


class PanService:
    @staticmethod
    async def call_external_api(
        pan: str,
        fastapi_request: Request,
        user_id: str
    ) -> Tuple[Response, Dict[str, Any], float]:
        """
        Call external API for PAN verification.

        Args:
            pan: PAN number to verify
            fastapi_request: FastAPI request object
            user_id: ID of the user making the request

        Returns:
            Tuple containing:
                - Response object
                - Parsed JSON response as dictionary
                - Turn around time in seconds
        """
        payload = {**PAN_PAYLOAD, "pan": pan}
        start_time = datetime.now()
        logger.info(f"Calling external API for PAN verification: {Config.EXTERNAL_API_URL_PAN}")
        response = requests.post(Config.EXTERNAL_API_URL_PAN, json=payload, headers=PAN_HEADERS)
        end_time = datetime.now()
        tat = (end_time - start_time).total_seconds()
        external_response = response.json()
        return response, external_response, tat


class RCService:
    @staticmethod
    async def call_external_api(
        reg_no: str,
        fastapi_request: Request,
        user_id: str
    ) -> Tuple[Response, Dict[str, Any], float]:
        """
        Call external API for vehicle registration verification.

        Args:
            reg_no: Vehicle registration number to verify
            fastapi_request: FastAPI request object
            user_id: ID of the user making the request

        Returns:
            Tuple containing:
                - Response object
                - Parsed JSON response as dictionary
                - Turn around time in seconds
        """
        payload = {**VEHICLE_PAYLOAD, "reg_no": reg_no}
        start_time = datetime.now()
        logger.info(f"Calling external API for Vehicle verification: {Config.EXTERNAL_API_URL_VEHICLE}")
        response = requests.post(Config.EXTERNAL_API_URL_VEHICLE, json=payload, headers=VEHICLE_HEADERS)
        end_time = datetime.now()
        tat = (end_time - start_time).total_seconds()
        external_response = response.json()
        return response, external_response, tat
