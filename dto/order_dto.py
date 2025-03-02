from typing import Optional
from pydantic import BaseModel, Field


class PanVerificationRequest(BaseModel):
    pan: str = Field(..., description="PAN Number to validate")


class VehicleVerificationRequest(BaseModel):
    reg_no: str


class PANResultDetail(BaseModel):
    pan_status: Optional[str] = None
    pan_type: Optional[str] = None
    pan: Optional[str] = None
    full_name: Optional[str] = None


class PanVerificationResponse(BaseModel):
    txn_id: Optional[str] = None
    pan: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    status_code: Optional[int] = None
    result: Optional[PANResultDetail] = None
    raw_response: Optional[dict] = None


class VehicleVerificationResponse(BaseModel):
    status: str
    reg_no: str
    state: Optional[str] = None
    owner_name: Optional[str] = None
    vehicle_manufacturer: Optional[str] = None
    model: Optional[str] = None
    registration_date: Optional[str] = None
    registration_valid_upto: Optional[str] = None
    insurance_valid_upto: Optional[str] = None
    pucc_valid_upto: Optional[str] = None
    raw_response: Optional[dict] = None
    message: Optional[str] = None

    class Config:
        exclude_none = True
