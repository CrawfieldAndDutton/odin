from typing import Dict, List
from decimal import Decimal

from repositories.user_ledger_transaction_repository import UserLedgerTransactionRepository
from repositories.user_repository import UserRepository

from dependencies.logger import logger
from dependencies.configuration import UserLedgerTransactionType

from services.email_service import EmailService


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
            # Get transactions from repository
            transactions = self.transaction_repository.get_weekly_service_stats(
                user_id, service_name
            )

            # Group transactions by date
            stats = {}
            for txn in transactions:
                date_key = txn.created_at.strftime("%Y-%m-%d")
                if date_key not in stats:
                    stats[date_key] = {
                        "count": 0,
                        "total_amount": Decimal(0)
                    }
                stats[date_key]["count"] += 1
                stats[date_key]["total_amount"] += abs(Decimal(str(txn.amount)))

            # Convert to list format and sort by date
            result = [
                {
                    "date": date,
                    "count": data["count"],
                    "total_amount": float(data["total_amount"])
                }
                for date, data in sorted(stats.items())
            ]

            logger.info(f"Weekly statistics for user {user_id} and service {service_name}: {result}")
            return result

        except Exception as e:
            logger.exception(
                f"Error getting weekly statistics for user {user_id} "
                f"and service {service_name}: {str(e)}"
            )
            raise e

    def get_user_monthly_statistics(self, user_id: str) -> Dict:
        """
        Get monthly statistics for a specific user.

        Args:
            user_id: ID of the user.

        Returns:
            Dict: Monthly statistics containing:
                - total_amount: Total amount spent in the month
                - total_hits: Total number of API calls in the month
                - service_wise_breakdown: Dictionary with service-wise statistics
        """
        try:
            # Get transactions from repository
            transactions = self.transaction_repository.get_monthly_service_stats(user_id)

            # Initialize statistics
            stats = {
                "total_amount": Decimal(0),
                "total_hits": 0,
                "service_wise_breakdown": {}
            }

            # Process each transaction
            for txn in transactions:
                # Skip credit transactions
                if txn.type == UserLedgerTransactionType.CREDIT.value:
                    continue

                # Update total amount and hits
                stats["total_amount"] += abs(Decimal(str(txn.amount)))
                stats["total_hits"] += 1

                # Update service-wise breakdown
                service_type = txn.type
                if service_type not in stats["service_wise_breakdown"]:
                    stats["service_wise_breakdown"][service_type] = {
                        "amount": Decimal(0),
                        "hits": 0
                    }
                stats["service_wise_breakdown"][service_type]["amount"] += abs(Decimal(str(txn.amount)))
                stats["service_wise_breakdown"][service_type]["hits"] += 1

            # Convert Decimal to float for JSON serialization
            stats["total_amount"] = float(stats["total_amount"])
            for service in stats["service_wise_breakdown"]:
                stats["service_wise_breakdown"][service]["amount"] = float(
                    stats["service_wise_breakdown"][service]["amount"]
                )

            logger.info(f"Monthly statistics for user {user_id}: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting monthly statistics for user {user_id}: {str(e)}")
            raise

    def capture_contact_us_lead(self, name: str, lead_email: str, company: str, phone: str, message: str) -> bool:
        """
        Capture and process a contact us form submission.

        Args:
            name: Full name of the person submitting the form
            lead_email: Email address of the lead
            company: Company name
            phone: Contact phone number
            message: Inquiry or message from the lead

        Returns:
            bool: True if the lead was successfully captured and processed, False otherwise

        Raises:
            ValueError: If any of the required fields are empty or invalid
            SMTPException: If there's an error sending the notification email
        """
        try:
            # Validate inputs
            if not all([name, lead_email, company, phone, message]):
                logger.error("Missing required fields in contact us form")
                raise ValueError("All fields are required")

            # Send notification email
            EmailService.send_contact_us_lead_email(name, lead_email, company, phone, message)

            logger.info(f"Successfully captured contact us lead for {lead_email}")
            return True

        except Exception as e:
            logger.exception(f"Error processing contact us lead: {str(e)}")
            return False
