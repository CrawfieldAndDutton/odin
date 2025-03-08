# Standard library imports
from datetime import datetime

# Third-party library imports
from mongoengine import (
    Document,
    StringField,
    BooleanField,
    FloatField,
    ListField,
    DateTimeField,
)
from pytz import timezone

# Define IST timezone
ist = timezone('Asia/Kolkata')


class APIClient(Document):
    user_id = StringField(required=True)
    client_id = StringField(required=True, unique=True)
    client_secret = StringField(required=True)
    is_enabled = BooleanField(default=True)
    credits = FloatField(default=0.0)
    enabled_apis = ListField(StringField(), default=list)
    created_at = DateTimeField(default=lambda: datetime.now(ist))
    updated_at = DateTimeField(default=lambda: datetime.now(ist))

    meta = {
        'collection': 'api_clients',
        'indexes': [
            'client_id',
            'is_enabled',
            'credits'
        ],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(ist)
        return super(APIClient, self).save(*args, **kwargs) 