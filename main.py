import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from mongoengine import connect
from dependencies.config import Config
from dependencies.middleware_log import log_middleware
from routes.user_router import router as user_router
from routes.kyc_router import pan_router, vehicle_router


# Generate secret keys if not set
if Config.SECRET_KEY == "YOUR_SECRET_KEY_HERE":
    print("WARNING: Using auto-generated SECRET_KEY.")
    Config.SECRET_KEY = secrets.token_hex(32)

if Config.REFRESH_SECRET_KEY == "YOUR_REFRESH_SECRET_KEY_HERE":
    print("WARNING: Using auto-generated REFRESH_SECRET_KEY.")
    Config.REFRESH_SECRET_KEY = secrets.token_hex(32)

# Initialize FastAPI app
app = FastAPI(title="KYC Verification API")
app.add_middleware(BaseHTTPMiddleware, dispatch=log_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Need to Specify frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connect(
    db=Config.MAIN_DB,
    host=Config.MONGO_URI,
    alias="kyc_fabric_db"
)


@app.get("/")
def read_root():
    return {"message": "Welcome to test!"}


# Register routers
app.include_router(user_router)
app.include_router(pan_router)
app.include_router(vehicle_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
