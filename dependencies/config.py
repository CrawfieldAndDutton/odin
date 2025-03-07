# Standard library imports
import os

# Third-party library imports
from dotenv import load_dotenv

load_dotenv()


class Config:
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
