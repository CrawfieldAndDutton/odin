from enum import Enum

from dependencies.configuration import AppConfiguration


class BaseEnum(Enum):

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class UserLedgerTransactionType(BaseEnum):
    """Enum for user ledger transaction types."""

    CREDIT = "CREDIT"
    KYC_PAN = "KYC_PAN"
    KYC_AADHAAR = "KYC_AADHAAR"
    KYC_VOTER = "KYC_VOTER"
    KYC_RC = "KYC_RC"
    KYC_DL = "KYC_DL"
    KYC_PASSPORT = "KYC_PASSPORT"
    EV_EMPLOYMENT_LATEST = "EV_EMPLOYMENT_LATEST"
    EV_EMPLOYMENT_HISTORY = "EV_EMPLOYMENT_HISTORY"
    KYB_GSTIN = "KYB_GSTIN"


PAN_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "aitan-pan-verification-apis.p.rapidapi.com",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

VEHICLE_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-key": AppConfiguration.RAPID_API_KEY,
}

AITAN_CONSENT_PAYLOAD = {
    "consent": "yes",
    "consent_text": "I hereby declare my consent agreement for fetching my information via AITAN Labs API",
}
