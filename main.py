from fastapi import FastAPI
from mongoengine import connect
from dependencies.config import Config, settings
import secrets
from routes.order_router import pan_router as pan_router
from routes.order_router import vehicle_router as vehicle_router
from routes.user_router import router as user_router


# Generate secret keys if not set
if settings.SECRET_KEY == "YOUR_SECRET_KEY_HERE":
    print("WARNING: Using auto-generated SECRET_KEY.")
    settings.SECRET_KEY = secrets.token_hex(32)

if settings.REFRESH_SECRET_KEY == "YOUR_REFRESH_SECRET_KEY_HERE":
    print("WARNING: Using auto-generated REFRESH_SECRET_KEY.")
    settings.REFRESH_SECRET_KEY = secrets.token_hex(32)

# Initialize FastAPI app
app = FastAPI(title="KYC Verification API")


connect(
    db=Config.MAIN_DB,
    host=Config.MONGO_URI,
    alias="kyc_fabric_db"
)


@app.get("/")
def read_root():
    return {"message": "Welcome to odin!"}


# Register routers
app.include_router(user_router)
app.include_router(pan_router)
app.include_router(vehicle_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
