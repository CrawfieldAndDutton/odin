# Standard library imports
from typing import Optional

# Local application imports
from dependencies.configuration import ServicePricing
from dependencies.constants import UserLedgerTransactionType
from dependencies.logger import logger

from models.user_ledger_transaction_model import UserLedgerTransaction

from repositories.user_ledger_transaction_repository import UserLedgerTransactionRepository


class UserLedgerTransactionHandler:
    """Handler for user ledger transaction operations."""

    def __init__(self):
        self.ledger_repository = UserLedgerTransactionRepository()

    def check_if_eligible(self, user_id: str, service_name: str) -> bool:
        """
        Check if user has sufficient credits for the service.

        Args:
            user_id: The user ID to check
            service_name: The service name from UserLedgerTransactionType

        Returns:
            bool: True if user has sufficient credits, False otherwise
        """
        try:
            # Validate service name
            if not UserLedgerTransactionType.has_value(service_name):
                logger.error(f"Invalid service name: {service_name}")
                return False

            # Get latest transaction to check balance
            latest_txn = self.ledger_repository.get_latest_ledger_txn_for_user(user_id)
            current_balance = latest_txn.balance if latest_txn else 0.0

            required_credits = ServicePricing.get_service_cost(service_name)
            return current_balance >= required_credits

        except Exception as e:
            logger.exception(f"Error checking eligibility for user {user_id}: {str(e)}")
            return False

    def deduct_credits(self, user_id: str, service_name: str) -> Optional[UserLedgerTransaction]:
        """
        Deduct credits for a service.

        Args:
            user_id: The user ID to deduct credits from
            service_name: The service name from UserLedgerTransactionType

        Returns:
            UserLedgerTransaction: The new transaction if successful, None otherwise
        """
        try:
            # Validate service name
            if not UserLedgerTransactionType.has_value(service_name):
                logger.error(f"Invalid service name: {service_name}")
                return None

            amount = ServicePricing.get_service_cost(service_name)
            
            # Create new transaction
            new_txn = self.ledger_repository.insert_ledger_txn_for_user(
                user_id=user_id,
                type=service_name,
                amount=-amount,  # Negative amount for deduction
                description=f"Credit deduction for {service_name}"
            )

            return new_txn
        
        except Exception as e:
            logger.exception(f"Error deducting credits for user {user_id}: {str(e)}")
            return None 