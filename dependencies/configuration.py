# Standard library imports
import os
from enum import Enum

# Third-party library imports
from dotenv import load_dotenv

load_dotenv()


class BaseEnum(Enum):

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class AppConfiguration:
    """Application configuration settings."""

    RAPID_API_KEY = os.getenv("RAPID_API_KEY")
    EXTERNAL_API_URL_PAN = os.getenv("EXTERNAL_API_URL_PAN")
    EXTERNAL_API_URL_VEHICLE = os.getenv("EXTERNAL_API_URL_VEHICLE")
    EXTERNAL_API_URL_VOTER = os.getenv("EXTERNAL_API_URL_VOTER")
    EXTERNAL_API_URL_DL = os.getenv("EXTERNAL_API_URL_DL")
    EXTERNAL_API_URL_PASSPORT = os.getenv("EXTERNAL_API_URL_PASSPORT")
    MONGO_URI = os.environ["MONGO_URI"]
    MAIN_DB = os.getenv("MAIN_DB", "kyc_fabric_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")  # Change in production!
    REFRESH_SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_REFRESH_SECRET_KEY_HERE")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


class ServicePricing:
    """Configuration for service pricing."""

    # KYC Service Costs
    KYC_PAN_COST = float(os.environ["KYC_PAN_COST"])
    KYC_AADHAAR_COST = float(os.environ["KYC_AADHAAR_COST"])
    KYC_VOTER_COST = float(os.environ["KYC_VOTER_COST"])
    KYC_RC_COST = float(os.environ["KYC_RC_COST"])
    KYC_DL_COST = float(os.environ["KYC_DL_COST"])
    KYC_PASSPORT_COST = float(os.environ["KYC_PASSPORT_COST"])

    # Employment Verification Service Costs
    EV_EMPLOYMENT_LATEST_COST = float(os.environ["EV_EMPLOYMENT_LATEST_COST"])
    EV_EMPLOYMENT_HISTORY_COST = float(os.environ["EV_EMPLOYMENT_HISTORY_COST"])

    # Business Verification Service Costs
    KYB_GSTIN_COST = float(os.environ["KYB_GSTIN_COST"])

    @classmethod
    def get_service_cost(cls, service_name: str) -> float:
        """Get the cost for a specific service."""
        cost_mapping = {
            UserLedgerTransactionType.KYC_PAN.value: cls.KYC_PAN_COST,
            UserLedgerTransactionType.KYC_AADHAAR.value: cls.KYC_AADHAAR_COST,
            UserLedgerTransactionType.KYC_VOTER.value: cls.KYC_VOTER_COST,
            UserLedgerTransactionType.KYC_RC.value: cls.KYC_RC_COST,
            UserLedgerTransactionType.KYC_DL.value: cls.KYC_DL_COST,
            UserLedgerTransactionType.KYC_PASSPORT.value: cls.KYC_PASSPORT_COST,
            UserLedgerTransactionType.EV_EMPLOYMENT_LATEST.value: cls.EV_EMPLOYMENT_LATEST_COST,
            UserLedgerTransactionType.EV_EMPLOYMENT_HISTORY.value: cls.EV_EMPLOYMENT_HISTORY_COST,
            UserLedgerTransactionType.KYB_GSTIN.value: cls.KYB_GSTIN_COST,
        }
        return cost_mapping.get(service_name, 0.0)


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


class KYCProvider(BaseEnum):
    """Enum for KYC providers."""

    AITAN = "AITAN"
    INTERNAL = "INTERNAL"
