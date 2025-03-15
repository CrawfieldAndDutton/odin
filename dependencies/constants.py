from dependencies.configuration import AppConfiguration


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


# Razorpay payment link payload
RAZORPAY_PAYMENT_LINK_PAYLOAD = {
    "currency": "INR",
    "accept_partial": False,
    "description": "",  # Will be dynamically set
    "customer": {
        "name": "",  # Will be dynamically set
        "email": "",  # Will be dynamically set
        "contact": ""  # Optional, can be added if available
    },
    "notify": {
        "sms": False,
        "email": True
    },
    "reminder_enable": True,
    "notes": {
        "user_id": "",  # Will be dynamically set
        "credits_purchased": ""  # Will be dynamically set
    },
    "callback_url": f"{AppConfiguration.BACKEND_BASE_URL}/dashboard/api/v1/payments/verify",
    "callback_method": "get"
}
