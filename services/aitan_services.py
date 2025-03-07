# Standard library imports
from typing import Tuple
from requests.models import Response

# Local application imports
from dependencies.constants import VEHICLE_HEADERS, AITAN_CONSENT_PAYLOAD, PAN_HEADERS
from dependencies.config import Config

from services.base_services import BaseService


class PanService(BaseService):
    @staticmethod
    async def call_external_api(
        pan: str,
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
        payload = {**AITAN_CONSENT_PAYLOAD, "pan": pan}
        return BaseService.call_external_api(Config.EXTERNAL_API_URL_PAN, PAN_HEADERS, payload)


class RCService(BaseService):
    @staticmethod
    async def call_external_api(
        reg_no: str,
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
        payload = {**AITAN_CONSENT_PAYLOAD, "reg_no": reg_no}
        return BaseService.call_external_api(Config.EXTERNAL_API_URL_VEHICLE, VEHICLE_HEADERS, payload)
