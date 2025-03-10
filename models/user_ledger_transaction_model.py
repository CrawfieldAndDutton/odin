# Standard library imports
from datetime import datetime

# Third-party library imports
from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField
)
from pytz import timezone

# Local application imports
from dependencies.configuration import UserLedgerTransactionType
from models.user_model import User

# Define IST timezone
ist = timezone('Asia/Kolkata')


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
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    description = StringField()

    meta = {
        'collection': 'user_ledger_transactions',
        'indexes': [
            'user_id',
            'type',
            'created_at'
        ],
        'ordering': ['-created_at'],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        """Override save to update `updated_at` timestamp."""
        self.updated_at = datetime.now(ist)
        return super().save(*args, **kwargs)
