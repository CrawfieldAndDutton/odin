# Standard library imports
from datetime import datetime
from typing import Optional

# Third-party library imports
from pydantic import BaseModel, Field


class UserLedgerTransaction(BaseModel):
    """Model for user ledger transactions."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    type: str
    amount: float
    description: str
    balance: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "user_id": "123",
                "type": "credit",
                "amount": 100.0,
                "description": "Initial credit",
                "balance": 100.0,
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        }
