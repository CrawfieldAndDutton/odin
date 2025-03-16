# Standard library imports
from typing import Optional
from datetime import datetime

# Standard library imports
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    role: Optional[str] = "user"
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[str] = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime


class TokenRefresh(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
    jti: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserOTPCreate(BaseModel):
    email: EmailStr
    phone_number: Optional[str] = None


class UserVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class UserVerifyResponse(BaseModel):
    email: EmailStr
    is_email_verified: bool


class ContactUsLead(BaseModel):
    name: str
    lead_email: EmailStr
    company: str
    phone: str
    message: str
