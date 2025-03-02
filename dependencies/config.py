import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class Config:
    RAPID_API_KEY = os.getenv("RAPID_API_KEY")
    PAN_API_URL = "https://aitan-pan-verification-apis.p.rapidapi.com/validation/api/v1/pan-basic"
    VEHICLE_API_URL = "https://vehicle-rc-verification-api3.p.rapidapi.com/api/v1/private/rc-v1"
    MONGO_URI = os.getenv("MONGO_URI")
    MAIN_DB = os.getenv("MAIN_DB", "kyc_fabric_db")
    if not MONGO_URI:
        raise ValueError(
            "MONGO_URI environment variable is required for MongoDB Atlas connection.")


class Settings(BaseSettings):
    APP_NAME: str = "Auth API"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")  # Change in production!
    REFRESH_SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_REFRESH_SECRET_KEY_HERE")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


settings = Settings()
