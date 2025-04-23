# Standard library imports
import time
from abc import ABC
from datetime import datetime
from typing import Dict, Any, Tuple

# Third-party library imports
import requests
import razorpay
from requests.models import Response
from fastapi import HTTPException

# Local application imports
from dependencies.logger import logger
from dependencies.configuration import RazorpayConfiguration


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
    def call_external_api(url: str,
                          headers: Dict[str, str],
                          payload: Dict[str, Any],
                          max_retries=3,
                          delay=1) -> Tuple[Response, float]:
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
        for attempt in range(max_retries):
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code not in [500, 501, 502, 503, 504]:
                break
            time.sleep(delay)
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
        end_time = datetime.now()
        tat = BaseService.calculate_tat(start_time, end_time)
        return response, tat

    @staticmethod
    def get_razorpay_client():
        """
        Get a configured Razorpay client.

        Returns:
            razorpay.Client: Configured Razorpay client
        """
        try:
            return razorpay.Client(auth=(RazorpayConfiguration.RAZORPAY_KEY_ID,
                                         RazorpayConfiguration.RAZORPAY_KEY_SECRET))
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {str(e)}")
            raise HTTPException(status_code=500, detail="Payment service unavailable")
