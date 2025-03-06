from datetime import datetime
from mongoengine import Document, StringField, BooleanField, FloatField
from mongoengine import IntField, DictField, DateTimeField
from pytz import timezone

# Define IST timezone
ist = timezone('Asia/Kolkata')


class KYCValidationTransaction(Document):

    # API and Provider Details
    api_name = StringField(required=True, choices=["PAN", "RC_V1"])  # PAN or RC
    provider_name = StringField(required=True, choices=[
                                "AITAN", "INTERNAL"])
    is_cached = BooleanField(default=False)

    # Performance Metrics
    tat = FloatField()  # Turnaround time (time taken for API to respond)
    # HTTP status code from the external API or internal response
    http_status_code = IntField()

    # Status and Message
    # Status of the transaction
    status = StringField(required=True, choices=[
                         "FOUND", "NOT_FOUND", "BAD_REQUEST", "TOO_MANY_REQUESTS", "ERROR"])
    message = StringField()

    # Transaction Details
    # Store user inputs (e.g., PAN, vehicle registration number)
    kyc_transaction_details = DictField()
    kyc_provider_request = DictField()  # Request payload sent to the provider
    kyc_provider_response = DictField()  # Raw response received from the provider

    # Transaction Logs
    # Logs for user requests (IP, user_agent, user_id, etc.)
    kyc_validation_transactions_logs = DictField()

    # User Details
    user_id = StringField(required=True)

    # Timestamps
    created_at = DateTimeField(default=lambda: datetime.now(ist))

    updated_at = DateTimeField(default=lambda: datetime.now(ist))

    # Meta Configuration
    meta = {
        "collection": "kyc_validation_transactions",
        "indexes": [
            "api_name",
            "provider_name",
            "is_cached",
            "user_id",
            "created_at",
        ],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        """Override save to update `updated_at` timestamp."""
        self.updated_at = datetime.now(ist)
        return super().save(*args, **kwargs)
