# Third-party library imports
from passlib.context import CryptContext

# Password context for hashing


class PasswordUtils:
    """Utility functions for password hashing and verification."""
    PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.

        Args:
            plain_password: The plain text password to verify.
            hashed_password: The hashed password to compare against.

        Returns:
            bool: True if the plain password matches the hashed password, False otherwise.
        """
        return PasswordUtils.PWD_CONTEXT.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generate a hash for a given password.

        Args:
            password: The plain text password to hash.

        Returns:
            str: The hashed password.
        """
        return PasswordUtils.PWD_CONTEXT.hash(password)
