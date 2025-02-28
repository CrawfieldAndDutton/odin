import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class Settings:
    PROJECT_NAME: str = "PAN Validation API"
    PROJECT_VERSION: str = "1.0.0"

    # API Keys
    PAN_API_KEY: str = os.getenv("PAN_API_KEY")  # type: ignore

    # MongoDB Config
    MONGODB_URI: str = os.getenv(
        "MONGODB_URI", "mongodb://localhost:27017/pan_validation")

    # API URLs
    PAN_VALIDATION_API_URL: str = "https://aitan-pan-verification-apis.p.rapidapi.com/validation/api/v1/pan-basic"

    # API Headers
    PAN_API_HEADERS: dict = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "aitan-pan-verification-apis.p.rapidapi.com",
        "x-rapidapi-key": PAN_API_KEY
    }


settings = Settings()
