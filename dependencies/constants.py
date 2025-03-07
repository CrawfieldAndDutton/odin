from dependencies.config import Config

PAN_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "aitan-pan-verification-apis.p.rapidapi.com",
    "x-rapidapi-key": Config.RAPID_API_KEY,
}

VEHICLE_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-key": Config.RAPID_API_KEY,
}

AITAN_CONSENT_PAYLOAD = {
    "consent": "yes",
    "consent_text": "I hereby declare my consent agreement for fetching my information via AITAN Labs API",
}
