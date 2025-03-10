# Standard library imports
from datetime import datetime

# Third-party library imports
from mongoengine import (
    Document,
    StringField,
    BooleanField,
    FloatField,
    IntField,
    DictField,
    DateTimeField,
)
from pytz import timezone

# Define IST timezone
ist = timezone('Asia/Kolkata')


class KYCValidationTransaction(Document):

    # API and Provider Details
    api_name = StringField(required=True)  
    provider_name = StringField(required=True, choices=["AITAN", "INTERNAL"])
    is_cached = BooleanField(default=False)
    tat = FloatField()  
    http_status_code = IntField()
    status = StringField(required=True, choices=["FOUND", "NOT_FOUND", "BAD_REQUEST", "TOO_MANY_REQUESTS", "ERROR"])
    message = StringField()
    kyc_transaction_details = DictField()  
    kyc_provider_request = DictField()  # Request payload sent to the provider
    kyc_provider_response = DictField()  # Raw response received from the provider
    user_id = StringField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(ist))
    updated_at = DateTimeField(default=lambda: datetime.now(ist))

    # Meta Configuration
    meta = {
        "collection": "kyc_validation_transactions",
        "indexes": [
            "api_name",
            "provider_name",
            "user_id",
            "created_at",
        ],
        'ordering': ['-created_at'],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        """Override save to update `updated_at` timestamp."""
        self.updated_at = datetime.now(ist)
        return super().save(*args, **kwargs)
