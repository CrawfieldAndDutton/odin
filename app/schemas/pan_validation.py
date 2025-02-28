from pydantic import BaseModel, Field
from typing import Optional, List


class PANValidationRequest(BaseModel):
    pan: str = Field(..., description="PAN Number to validate")


class PANResultDetail(BaseModel):
    pan_status: Optional[str] = None
    pan_type: Optional[str] = None
    pan: Optional[str] = None
    full_name: Optional[str] = None


class PANValidationResponse(BaseModel):
    txn_id: str
    status: str
    message: str
    status_code: int
    result: PANResultDetail


class PANHistoryItem(BaseModel):
    txn_id: str
    status: Optional[str] = None
    message: Optional[str] = None
    status_code: Optional[int] = None
    pan_status: Optional[str] = None
    pan_type: Optional[str] = None
    pan: str
    full_name: Optional[str] = None
    created_at: Optional[str] = None


class PANHistoryResponse(BaseModel):
    history: List[PANHistoryItem]
