from typing import Optional
from pydantic import BaseModel, Field


class PanVerificationRequest(BaseModel):
    pan: str = Field(..., description="PAN Number to validate")


class VehicleVerificationRequest(BaseModel):
    reg_no: str = Field(..., description="Vehicle Registration Number to validate")


class APISuccessResponse(BaseModel):
    http_status_code: Optional[int] = Field(None, description="HTTP Status Code")
    message: Optional[str] = Field(None, description="Message from the verification process")
    result: Optional[dict] = Field(None, description="Raw response from the verification process")

    class Config:
        exclude_none = True
