# Third-party library imports
from pydantic import BaseModel, Field


class PanVerificationRequest(BaseModel):
    pan: str = Field(..., description="PAN Number to validate")


class VehicleVerificationRequest(BaseModel):
    reg_no: str = Field(..., description="Vehicle Registration Number to validate")


class VoterVerificationRequest(BaseModel):
    epic_no: str = Field(..., description="Epic Number to validate")


class DLVerificationRequest(BaseModel):
    dl_no: str = Field(..., description="DL Number to validate")
    dob: str = Field(..., description="DOB to validate")


class PassportVerificationRequest(BaseModel):
    file_number: str = Field(..., description="Passport Number to validate")
    dob: str = Field(..., description="DOB to validate")
    name: str = Field(..., description="Name to validate")
