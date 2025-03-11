from datetime import datetime
# Third-party library imports
from pydantic import BaseModel, Field, validator


class PanVerificationRequest(BaseModel):
    pan: str = Field(..., description="PAN Number to validate")


class VehicleVerificationRequest(BaseModel):
    reg_no: str = Field(..., description="Vehicle Registration Number to validate")


class VoterVerificationRequest(BaseModel):
    epic_no: str = Field(..., description="Epic Number to validate")


class DLVerificationRequest(BaseModel):
    dl_no: str = Field(..., description="DL Number to validate")
    dob: str = Field(..., description="DOB to validate")

    @staticmethod
    def convert_to_dd_mm_yyyy(date_str: str) -> str:
        """
        Convert any date format to dd-mm-yyyy format.
        """
        # List of possible date formats to try
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y',  # DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
            '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',  # YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
            '%m-%d-%Y', '%m/%d/%Y', '%m.%d.%Y',  # MM-DD-YYYY, MM/DD/YYYY, MM.DD.YYYY
            '%d-%m-%y', '%d/%m/%y', '%d.%m.%y',  # DD-MM-YY, DD/MM/YY, DD.MM.YY
            '%y-%m-%d', '%y/%m/%d', '%y.%m.%d',  # YY-MM-DD, YY/MM/DD, YY.MM.DD
            '%m-%d-%y', '%m/%d/%y', '%m.%d.%y',  # MM-DD-YY, MM/DD/YY, MM.DD.YY
        ]

        for fmt in date_formats:
            try:
                # Try to parse the date string using the current format
                date_obj = datetime.strptime(date_str, fmt)
                # If successful, format it to dd-mm-yyyy
                return date_obj.strftime('%d-%m-%Y')
            except ValueError:
                continue

        # If no format matches, raise an error
        raise ValueError(
            f"Unable to parse the date: {date_str}. Supported formats include DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.")

    @validator("dob")
    def validate_and_convert_dob(cls, value):
        """
        Validate and convert the dob to dd-mm-yyyy format.
        """
        return cls.convert_to_dd_mm_yyyy(value)


class PassportVerificationRequest(BaseModel):
    file_number: str = Field(..., description="Passport Number to validate")
    dob: str = Field(..., description="DOB to validate")
    name: str = Field(..., description="Name to validate")
