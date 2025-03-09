# Standard library imports
from typing import Optional

# Third-party library imports
from mongoengine.errors import DoesNotExist

# Local application imports
from dependencies.logger import logger

from models.user_ledger_transaction_model import UserLedgerTransaction

from repositories.user_repository import UserRepository


class UserLedgerTransactionRepository:
    """Repository for user ledger transactions."""

    def __init__(self):
        self.user_repository = UserRepository()

    @staticmethod
    def get_latest_ledger_txn_for_user(user_id: str) -> Optional[UserLedgerTransaction]:
        """Get the latest ledger transaction for a user."""
        try:
            return UserLedgerTransaction.objects(user_id=user_id).order_by('-created_at').first()
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting latest ledger transaction for user {user_id}: {str(e)}")
            raise

    async def insert_ledger_txn_for_user(
        self,
        user_id: str,
        type: str,
        amount: float,
        description: str
    ) -> UserLedgerTransaction:
        """Insert a new ledger transaction for a user."""
        try:
            # Get the latest transaction to calculate the new balance
            latest_txn = self.get_latest_ledger_txn_for_user(user_id)
            current_balance = latest_txn.balance if latest_txn else 0.0

            # Calculate new balance based on transaction type
            new_balance = current_balance + amount

            # Create new transaction
            new_txn = UserLedgerTransaction(
                user_id=user_id,
                type=type,
                amount=amount,
                description=description,
                balance=new_balance
            )
            new_txn.save()

            # Update user credits to match the new balance
            await self.user_repository.update_user_credits(int(user_id), new_txn)

            return new_txn
        except Exception as e:
            logger.error(f"Error inserting ledger transaction for user {user_id}: {str(e)}")
            raise
