# Standard library imports
from typing import Tuple
from requests.models import Response

# Local application imports
from dependencies.constants import VEHICLE_HEADERS, AITAN_CONSENT_PAYLOAD, PAN_HEADERS
from dependencies.constants import VOTER_HEADERS, DL_HEADERS, PASSPORT_HEADERS, AADHAAR_HEADERS
from dependencies.configuration import AppConfiguration

from services.base_services import BaseService


class PanService(BaseService):
    @staticmethod
    def call_external_api(
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
        return BaseService.call_external_api(AppConfiguration.EXTERNAL_API_URL_PAN, PAN_HEADERS, payload)


class RCService(BaseService):
    @staticmethod
    def call_external_api(
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
        return BaseService.call_external_api(AppConfiguration.EXTERNAL_API_URL_VEHICLE, VEHICLE_HEADERS, payload)


class VoterService(BaseService):
    @staticmethod
    def call_external_api(
        epic_no: str,
    ) -> Tuple[Response, float]:
        """
        Call external API for voter verification.

        Args:
            epic_no: Epic number to verify

        Returns:
            Tuple containing:
                - Response object
                - Turn around time in seconds
        """
        payload = {**AITAN_CONSENT_PAYLOAD, "epic_no": epic_no}
        return BaseService.call_external_api(AppConfiguration.EXTERNAL_API_URL_VOTER, VOTER_HEADERS, payload)


class DLService(BaseService):
    @staticmethod
    def call_external_api(
        dl_no: str,
        dob: str,
    ) -> Tuple[Response, float]:
        """
        Call external API for DL verification.
        """
        payload = {**AITAN_CONSENT_PAYLOAD, "dl_no": dl_no, "dob": dob}
        return BaseService.call_external_api(AppConfiguration.EXTERNAL_API_URL_DL, DL_HEADERS, payload)


class PassportService(BaseService):
    @staticmethod
    def call_external_api(
        file_number: str,
        dob: str,
        name: str,
    ) -> Tuple[Response, float]:
        """
        Call external API for passport verification.
        """
        payload = {**AITAN_CONSENT_PAYLOAD, "file_number": file_number, "dob": dob, "name": name}
        return BaseService.call_external_api(AppConfiguration.EXTERNAL_API_URL_PASSPORT, PASSPORT_HEADERS, payload)


class AadhaarService(BaseService):
    @staticmethod
    def call_external_api(
        aadhaar: str,
    ) -> Tuple[Response, float]:
        """
        Call external API for aadhaar verification.
        """
        payload = {**AITAN_CONSENT_PAYLOAD, "aadhaar": aadhaar}
        return BaseService.call_external_api(AppConfiguration.EXTERNAL_API_URL_AADHAAR, AADHAAR_HEADERS, payload)
