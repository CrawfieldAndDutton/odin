# Standard library imports
from abc import ABC
from datetime import datetime
from typing import Dict, Any, Tuple

# Third-party library imports
import requests
from requests.models import Response

# Local application imports
from dependencies.logger import logger


class BaseService(ABC):
    @staticmethod
    def calculate_tat(start_time: datetime, end_time: datetime) -> float:
        """
    Calculate turnaround time (TAT) in seconds.

    Args:
        start_time: The start time of the process.
        end_time: The end time of the process.

    Returns:
        float: Turnaround time in seconds.
    """
        return (end_time - start_time).total_seconds()

    @staticmethod
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
        tat = BaseService.calculate_tat(start_time, end_time)
        return response, tat
