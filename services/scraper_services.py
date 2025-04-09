from typing import Tuple
from requests.models import Response

# Local application imports
from dependencies.configuration import AppConfiguration
from dependencies.constants import GSTIN_HEADERS, get_random_user_agent

from services.base_services import BaseService


class GSTINService(BaseService):
    @staticmethod
    def call_external_api(
        gstin: str,
    ) -> Tuple[Response, float]:
        """
        Call external API for GSTIN verification.

        Args:
            gstin: GSTIN number to verify

        Returns:
            Tuple containing:
                - Response object
                - Turn around time in seconds
        """
        URL = f"{AppConfiguration.EXTERNAL_API_URL_GSTIN}/{gstin}"
        payload = {}
        GSTIN_HEADERS["User-Agent"] = get_random_user_agent()
        print(GSTIN_HEADERS)
        return BaseService.call_external_api(URL, GSTIN_HEADERS, payload)
