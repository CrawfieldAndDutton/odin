from typing import Optional, Any
from pydantic import BaseModel, Field


class APISuccessResponse(BaseModel):
    """Common response model for API endpoints."""
    http_status_code: Optional[int] = Field(None, description="HTTP Status Code")
    message: Optional[str] = Field(None, description="Message from the process")
    result: Optional[Any] = Field(None, description="Response data from the process")

    class Config:
        exclude_none = True
