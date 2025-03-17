from pytz import timezone
from datetime import datetime, timedelta

from dependencies.configuration import AppConfiguration

# Define IST timezone
IST = timezone('Asia/Kolkata')

PAN_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "aitan-pan-verification-apis.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

VEHICLE_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

VOTER_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "voter-id-verification-api.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

DL_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "dl-verification-api1.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

PASSPORT_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "passport-verification-api1.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

AADHAAR_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "aadhaar-to-pan-api.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

AITAN_CONSENT_PAYLOAD = {
    "consent": "yes",
    "consent_text": "I hereby declare my consent agreement for fetching my information via AITAN Labs API",
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
