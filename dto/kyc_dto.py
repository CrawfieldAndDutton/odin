# Standard library imports
from typing import Optional

# Third-party library imports
from pydantic import BaseModel, Field


class PanVerificationRequest(BaseModel):
    pan: str = Field(..., description="PAN Number to validate")


class VehicleVerificationRequest(BaseModel):
    reg_no: str = Field(..., description="Vehicle Registration Number to validate")
