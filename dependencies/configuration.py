# Standard library imports
import os

# Third-party library imports
from dotenv import load_dotenv

# Local application imports
from dependencies.constants import UserLedgerTransactionType

load_dotenv()


class AppConfiguration:
    """Application configuration settings."""

    RAPID_API_KEY = os.getenv("RAPID_API_KEY")
    EXTERNAL_API_URL_PAN = os.getenv("EXTERNAL_API_URL_PAN")
    EXTERNAL_API_URL_VEHICLE = os.getenv("EXTERNAL_API_URL_VEHICLE")
    MONGO_URI = os.environ["MONGO_URI"]
    MAIN_DB = os.getenv("MAIN_DB", "kyc_fabric_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")  # Change in production!
    REFRESH_SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_REFRESH_SECRET_KEY_HERE")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


class ServicePricing:
    """Configuration for service pricing."""

    # KYC Services
    KYC_PAN_COST = float(os.environ["KYC_PAN_COST"])
    KYC_AADHAAR_COST = float(os.environ["KYC_AADHAAR_COST"])
    KYC_VOTER_COST = float(os.environ["KYC_VOTER_COST"])
    KYC_RC_COST = float(os.environ["KYC_RC_COST"])
    KYC_DL_COST = float(os.environ["KYC_DL_COST"])
    KYC_PASSPORT_COST = float(os.environ["KYC_PASSPORT_COST"])

    # Employment Verification Services
    EV_EMPLOYMENT_LATEST_COST = float(os.environ["EV_EMPLOYMENT_LATEST_COST"])
    EV_EMPLOYMENT_HISTORY_COST = float(os.environ["EV_EMPLOYMENT_HISTORY_COST"])

    # Business Verification Services
    KYB_GSTIN_COST = float(os.environ["KYB_GSTIN_COST"])

    @classmethod
    def get_service_cost(cls, service_name: str) -> float:
        """Get the cost for a specific service."""
        cost_mapping = {
            UserLedgerTransactionType.KYC_PAN: cls.KYC_PAN_COST,
            UserLedgerTransactionType.KYC_AADHAAR: cls.KYC_AADHAAR_COST,
            UserLedgerTransactionType.KYC_VOTER: cls.KYC_VOTER_COST,
            UserLedgerTransactionType.KYC_RC: cls.KYC_RC_COST,
            UserLedgerTransactionType.KYC_DL: cls.KYC_DL_COST,
            UserLedgerTransactionType.KYC_PASSPORT: cls.KYC_PASSPORT_COST,
            UserLedgerTransactionType.EV_EMPLOYMENT_LATEST: cls.EV_EMPLOYMENT_LATEST_COST,
            UserLedgerTransactionType.EV_EMPLOYMENT_HISTORY: cls.EV_EMPLOYMENT_HISTORY_COST,
            UserLedgerTransactionType.KYB_GSTIN: cls.KYB_GSTIN_COST,
        }
        return cost_mapping.get(service_name, 0.0) 