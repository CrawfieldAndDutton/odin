# Standard library imports
from typing import Dict, List
from datetime import datetime, timedelta, UTC

# Local application imports
from dependencies.logger import logger

from models.user_ledger_transaction_model import UserLedgerTransaction

from repositories.user_repository import UserRepository


class UserLedgerTransactionRepository:
    """Repository for user ledger transactions."""

    def __init__(self):
        self.user_repository = UserRepository()

    def insert_ledger_txn_for_user(
        self,
        user_id: str,
        type: str,
        amount: float,
        description: str
    ) -> UserLedgerTransaction:
        """Insert a new ledger transaction for a user."""
        try:
            # Get the latest transaction to calculate the new balance
            current_balance = self.user_repository.get_user_by_id(user_id).credits
            logger.info(
                f"Getting user {user_id} credits before inserting ledger transaction {type} {amount} {current_balance}")

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
            user = self.user_repository.get_user_by_id(user_id)
            user.credits = new_balance
            user.save()
            logger.info(f"Updated user {user_id} credits to {new_balance} for transaction {type} {amount}")

            return new_txn
        except Exception as e:
            logger.error(f"Error inserting ledger transaction for user {user_id}: {str(e)}")
            raise

    def get_service_usage_count(self, user_id: str) -> Dict[str, int]:
        """Get count of transactions by service type for a user in the last 30 days."""
        try:
            thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
            transactions = UserLedgerTransaction.objects(
                user_id=user_id,
                created_at__gte=thirty_days_ago
            )
            service_types = transactions.distinct("type")
            return {
                service_type: transactions.filter(type=service_type).count()
                for service_type in service_types
            }
        except Exception as e:
            logger.error(f"Error getting service usage count for user {user_id}: {str(e)}")
            return {}

    def get_weekly_service_stats(self, user_id: str, service_name: str) -> List[Dict]:
        """Get weekly statistics for a specific service."""
        try:
            week_ago = datetime.now(UTC) - timedelta(days=7)

            # Get all transactions for the service in the last week
            transactions = UserLedgerTransaction.objects(
                user_id=user_id,
                type=service_name,
                created_at__gte=week_ago
            ).order_by('created_at')

            # Group transactions by date
            stats = {}
            for txn in transactions:
                date_key = txn.created_at.strftime("%Y-%m-%d")
                if date_key not in stats:
                    stats[date_key] = {
                        "count": 0,
                        "total_amount": 0.0
                    }
                stats[date_key]["count"] += 1
                stats[date_key]["total_amount"] += txn.amount

            # Convert to list format
            return [
                {
                    "date": date,
                    "count": data["count"],
                    "total_amount": data["total_amount"]
                }
                for date, data in sorted(stats.items())
            ]
        except Exception as e:
            logger.error(f"Error getting weekly service stats for user {user_id}: {str(e)}")
            return []

    def get_user_ledger_transactions(self, user_id: str) -> List[UserLedgerTransaction]:
        """Get all ledger transactions for a user."""
        try:
            return UserLedgerTransaction.objects(user_id=user_id).order_by('-created_at')
        except Exception as e:
            logger.exception(f"Error getting ledger transactions for user {user_id}: {str(e)}")
            return []
