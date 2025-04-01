# Third-party library imports
from pydantic import BaseModel, Field, field_validator
from typing import Optional

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

    @field_validator("dob")
    def validate_and_convert_dob(cls, value):
        """
        Validate and convert the dob to dd-mm-yyyy format.
        """
        return convert_to_dd_mm_yyyy(value)


class PassportVerificationRequest(BaseModel):
    file_number: str = Field(..., description="Passport Number to validate")
    dob: str = Field(..., description="DOB to validate")
    name: str = Field(..., description="Name to validate")


class AadhaarVerificationRequest(BaseModel):
    aadhaar: str = Field(..., description="Aadhaar Number to validate")


class MobileLookupVerificationRequest(BaseModel):
    mobile: str = Field(..., description="Mobile Number to validate")


class EmploymentLatestVerificationRequest(BaseModel):
    uan: Optional[str] = Field(None, description="UAN Number to validate")
    pan: Optional[str] = Field(None, description="PAN Number to validate")
    mobile: Optional[str] = Field(None, description="Mobile Number to validate")
    dob: Optional[str] = Field(None, description="Date of Birth to validate")
    employer_name: Optional[str] = Field(None, description="Employer Name to validate")
    employee_name: Optional[str] = Field(None, description="Employee Name to validate")

    # @field_validator("dob")
    # def validate_and_convert_dob(cls, value):
    #     """
    #     Validate and convert the dob to yyyy-mm-dd format.
    #     """
    #     return convert_to_yyyy_mm_dd(value)
