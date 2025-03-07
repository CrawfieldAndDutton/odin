# Standard library imports
# (None in this case)

# Third-party library imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from mongoengine import connect

# Local application imports
from dependencies.config import Config
from dependencies.middleware_log import log_middleware

from routes.user_router import auth_router
from routes.kyc_router import kyc_router


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
    return {"message": "Welcome to odin!"}


# Register routers
app.include_router(auth_router)
app.include_router(kyc_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info",
                workers=1,
                timeout_keep_alive=5
                )
