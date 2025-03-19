# Third-party library imports
from pydantic import BaseModel, Field, validator

# Local application imports
from dependencies.date_utils import convert_to_dd_mm_yyyy


class PanVerificationRequest(BaseModel):
    pan: str = Field(..., description="PAN Number to validate")


class VehicleVerificationRequest(BaseModel):
    reg_no: str = Field(..., description="Vehicle Registration Number to validate")


class VoterVerificationRequest(BaseModel):
    epic_no: str = Field(..., description="Epic Number to validate")


class DLVerificationRequest(BaseModel):
    dl_no: str = Field(..., description="DL Number to validate")
    dob: str = Field(..., description="DOB to validate")

    @validator("dob")
    def validate_and_convert_dob(cls, value):
        """
        Validate and convert the dob to dd-mm-yyyy format.
        """
        return convert_to_dd_mm_yyyy(value)


class PassportVerificationRequest(BaseModel):
    file_number: str = Field(..., description="Passport Number to validate")
    dob: str = Field(..., description="DOB to validate")
    name: str = Field(..., description="Name to validate")

    @validator("dob")
    def validate_and_convert_dob(cls, value):
        """
        Validate and convert the dob to dd-mm-yyyy format.
        """
        return convert_to_dd_mm_yyyy(value)


class AadhaarVerificationRequest(BaseModel):
    aadhaar: str = Field(..., description="Aadhaar Number to validate")


class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="Email to reset password")
    password: str = Field(..., description="New password to set")
