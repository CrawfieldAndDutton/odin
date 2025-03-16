# Standard library imports
from typing import Optional, List, Dict

# Local application imports
from dependencies.configuration import ServicePricing, UserLedgerTransactionType
from dependencies.logger import logger

from models.user_ledger_transaction_model import UserLedgerTransaction

from repositories.user_ledger_transaction_repository import UserLedgerTransactionRepository
from repositories.user_repository import UserRepository


class UserLedgerTransactionHandler:
    """Handler for user ledger transaction operations."""

    def __init__(self):
        self.ledger_repository = UserLedgerTransactionRepository()

        self.user_repository = UserRepository()

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
            current_balance = self.user_repository.get_user_by_id(user_id).credits

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
                amount=-amount,
                description=f"Credit deduction for {service_name}"
            )

            return new_txn

        except Exception as e:
            logger.exception(f"Error deducting credits for user {user_id}: {str(e)}")
            return None

    def increase_credits(self, user_id: str, amount: float) -> Optional[UserLedgerTransaction]:
        """
        Increase user credits.

        Args:
            user_id: The user ID to increase credits for
            amount: The amount of credits to increase

        Returns:
            UserLedgerTransaction: The new transaction if successful, None otherwise
        """
        return self.ledger_repository.insert_ledger_txn_for_user(
            user_id,
            UserLedgerTransactionType.CREDIT.value,
            amount,
            "Credits Purchased"
        )

    def get_user_ledger_transactions(self, user_id: str, page: int = 1) -> tuple[List[Dict], int]:
        """
        Get all ledger transactions for a user in a paginated manner.

        Args:
            user_id: The user ID to get ledger transactions for
            page: The page number to get

        Returns:
            tuple[List[Dict], int]: The list of ledger transactions as dictionaries and the
            total number of transactions
        """
        if page < 1:
            # Handle invalid page number
            page = 1

        limit = 100
        offset = (page - 1) * limit

        # Get all transactions
        all_transactions = self.ledger_repository.get_user_ledger_transactions(user_id)
        total_transactions = len(all_transactions)

        # Apply pagination
        start_idx = offset
        end_idx = min(offset + limit, total_transactions)
        paginated_transactions = all_transactions[start_idx:end_idx] if start_idx < total_transactions else []

        # Convert transactions to dictionaries
        transaction_dicts = []
        for txn in paginated_transactions:
            event_dict = txn.to_mongo()
            event_dict.pop('_id', None)  # Remove MongoDB _id field
            transaction_dicts.append(event_dict)

        return transaction_dicts, total_transactions
