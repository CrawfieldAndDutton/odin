from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import connect_to_mongodb, close_mongodb_connection
from app.api.endpoints import pan_validation

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Events


@app.on_event("startup")
def startup_db_client():
    connect_to_mongodb()


@app.on_event("shutdown")
def shutdown_db_client():
    close_mongodb_connection()

# Root endpoint


@app.get("/")
async def root():
    return {"message": f"{settings.PROJECT_NAME} v{settings.PROJECT_VERSION}"}

# Include routers
app.include_router(pan_validation.router, prefix="/api/v1", tags=["PAN Validation"])
