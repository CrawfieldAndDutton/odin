# Standard library imports
from datetime import datetime

# Third-party library imports
from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField
)

# Local application imports
from dependencies.constants import IST
from dependencies.configuration import AppConfiguration


class UserLedgerTransaction(Document):
    """
    Model for storing user ledger transactions.

    Attributes:
        user (ReferenceField): Reference to the User model
        transaction_type (EnumField): Type of transaction (e.g., KYC_PAN, KYC_RC)
        amount (FloatField): Transaction amount
        status (EnumField): Status of the transaction (e.g., PENDING, COMPLETED)
        created_at (DateTimeField): Timestamp when transaction was created
        updated_at (DateTimeField): Timestamp when transaction was last updated
        description (StringField): Optional description of the transaction
    """
    user_id = StringField(required=True)
    type = StringField(required=True)
    amount = FloatField(required=True)
    description = StringField(required=True)
    balance = FloatField(required=True)
    created_at = DateTimeField(default=datetime.now(IST))
    updated_at = DateTimeField(default=datetime.now(IST))
    description = StringField()

    meta = {
        'collection': 'user_ledger_transactions',
        'indexes': [
            'user_id',
            'type'
        ],
        'ordering': ['-created_at'],
        "db_alias": AppConfiguration.MAIN_DB
    }

    def save(self, *args, **kwargs):
        """Override save to update `updated_at` timestamp."""
        self.updated_at = datetime.now(IST)
        return super().save(*args, **kwargs)
