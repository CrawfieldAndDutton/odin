# Third-party library imports
from fastapi import HTTPException, status

# Error message constants
INVALID_REFRESH_TOKEN_MSG = "Invalid refresh token"


class CredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


class UserAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or phone number already exists",
        )


class InsufficientCreditsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits to perform this operation",
        )


class OTPVerificationError(HTTPException):
    def __init__(self, detail: str = "OTP verification failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
