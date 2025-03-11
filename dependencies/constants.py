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

AITAN_CONSENT_PAYLOAD = {
    "consent": "yes",
    "consent_text": "I hereby declare my consent agreement for fetching my information via AITAN Labs API",
}
