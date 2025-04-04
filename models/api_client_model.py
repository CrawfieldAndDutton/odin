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

# Local application imports
from dependencies.constants import IST
from dependencies.configuration import AppConfiguration


class APIClient(Document):
    user_id = StringField(required=True)
    client_id = StringField(required=True, unique=True)
    client_secret = StringField(required=True)
    is_enabled = BooleanField(default=True)
    credits = FloatField(default=0.0)
    enabled_apis = ListField(StringField(), default=list)
    created_at = DateTimeField(default=lambda: datetime.now(IST))
    updated_at = DateTimeField(default=lambda: datetime.now(IST))

    meta = {
        'collection': 'api_clients',
        'indexes': [
            'client_id',
            'is_enabled',
            'credits'
        ],
        "db_alias": AppConfiguration.MAIN_DB
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(IST)
        return super(APIClient, self).save(*args, **kwargs)
