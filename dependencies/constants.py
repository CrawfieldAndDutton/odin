import json
import random
from pathlib import Path
from pytz import timezone
from datetime import datetime, timedelta

from dependencies.configuration import AppConfiguration
from dependencies.logger import logger

# Define IST timezone
IST = timezone('Asia/Kolkata')

CONTENT_TYPE = "application/json"

JSON_PATH = Path(__file__).parent / "scraper_utils.json"
logger.info(f"Loading user agents from {JSON_PATH}")

with open(JSON_PATH, 'r') as f:
    USER_AGENTS = json.load(f)["USER_AGENTS"]


def get_random_user_agent() -> str:
    """
    Generate a random User-Agent string.
    """
    return random.choice(USER_AGENTS)


PAN_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-host": "aitan-pan-verification-apis.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

VEHICLE_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

VOTER_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-host": "voter-id-verification-api.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

DL_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-host": "dl-verification-api1.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

PASSPORT_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-host": "passport-verification-api1.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

AADHAAR_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-host": "aadhaar-to-pan-api.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

MOBILE_LOOKUP_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-host": "digital-footprint-api1.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

EMPLOYMENT_LATEST_HEADERS = {
    "Content-Type": CONTENT_TYPE,
    "x-rapidapi-host": "employment-verification.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

GSTIN_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-GB,en;q=0.7',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
}


AITAN_CONSENT_PAYLOAD = {
    "consent": "yes",
    "consent_text": "I hereby declare my consent agreement for fetching my information via AITAN Labs API",
}
EMPLOYMENT_LATEST_CONSENT_PAYLOAD = {
    "consent": "yes",
    "consent_text": "I give my consent to UAN Latest V2 api to check my employment details",
}

# Calculate expiry time (30 minutes from now)


def get_expiry_timestamp():
    return int((datetime.now(IST) + timedelta(minutes=30)).timestamp())


# Razorpay payment link payload
RAZORPAY_PAYMENT_LINK_PAYLOAD = {
    "currency": "INR",
    "accept_partial": False,
    "description": "",
    "customer": {
        "name": "",
        "email": "",
        "contact": ""
    },
    "notify": {
        "sms": True,
        "email": True
    },
    "reminder_enable": True,
    "notes": {
        "user_id": "",
        "credits_purchased": ""
    },
    "callback_url": f"{AppConfiguration.BACKEND_BASE_URL}/dashboard/api/v1/payments/verify",
    "callback_method": "get",
    "expire_by": get_expiry_timestamp()
}
