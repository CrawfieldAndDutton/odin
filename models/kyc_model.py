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

# Local application imports
from dependencies.constants import IST
from dependencies.configuration import AppConfiguration

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
    created_at = DateTimeField(default=lambda: datetime.now(IST))
    updated_at = DateTimeField(default=lambda: datetime.now(IST))

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
        "db_alias": AppConfiguration.MAIN_DB
    }

    def save(self, *args, **kwargs):
        """Override save to update `updated_at` timestamp."""
        self.updated_at = datetime.now(IST)
        return super().save(*args, **kwargs)
