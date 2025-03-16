from typing import Dict, List
from datetime import datetime, IST
from smtplib import SMTPException

from repositories.user_ledger_transaction_repository import UserLedgerTransactionRepository
from repositories.user_repository import UserRepository

from dependencies.logger import logger
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

            # Process the lead (existing code here)
            lead_data = {
                "name": name,
                "email": lead_email,
                "company": company,
                "phone": phone,
                "message": message,
                "created_at": datetime.now(IST)
            }

            # Send notification email
            EmailService.send_contact_us_notification(lead_data)

            logger.info(f"Successfully captured contact us lead for {lead_email}")
            return True

        except Exception as e:
            logger.exception(f"Error processing contact us lead: {str(e)}")
            return False
