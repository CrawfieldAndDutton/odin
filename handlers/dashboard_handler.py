from typing import Dict, List

from repositories.user_ledger_transaction_repository import UserLedgerTransactionRepository
from repositories.user_repository import UserRepository

from dependencies.logger import logger


class DashboardHandler:

    def __init__(self):
        self.transaction_repository = UserLedgerTransactionRepository()
        self.user_repository = UserRepository()

    def get_user_summarized_count(self, user_id: str) -> Dict[str, int]:
        """
        Get summarized count of all services used by the user.

        Args:
            user_id (str): The ID of the user

        Returns:
            Dict[str, int]: Dictionary with service types as keys and their usage counts as values
        """
        return self.transaction_repository.get_service_usage_count(user_id)

    def get_user_pending_credits(self, user_id: str) -> float:
        """
        Get total pending credits for the user.

        Args:
            user_id (str): The ID of the user

        Returns:
            float: Total pending credits amount
        """
        user_obj = self.user_repository.get_user_by_id(user_id)
        return user_obj.credits

    def get_user_weekly_statistics(self, user_id: str, service_name: str) -> List[Dict]:
        """
        Get weekly statistics for a specific service used by the user.

        Args:
            user_id (str): The ID of the user
            service_name (str): The name of the service to get statistics for

        Returns:
            List[Dict]: List of daily statistics containing count and total amount
        """
        try:
            stats = self.transaction_repository.get_weekly_service_stats(
                user_id, service_name
            )
            return [
                {
                    "date": stat["date"],
                    "count": stat["count"],
                    "total_amount": abs(stat["total_amount"])  # changes
                }
                for stat in stats
            ]
        except Exception as e:
            logger.error(
                f"Error getting weekly statistics for user {user_id} "
                f"and service {service_name}: {str(e)}"
            )
            raise e
