# Standard library imports
from datetime import datetime

# Third-party library imports
from mongoengine import (
    Document,
    StringField,
    BooleanField,
    EmailField,
    DateTimeField,
    FloatField,
)
from pytz import timezone

# Define IST timezone
ist = timezone('Asia/Kolkata')


class User(Document):
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    hashed_password = StringField(required=True)
    first_name = StringField()
    last_name = StringField()
    role = StringField(default="user", choices=["user", "admin"])
    is_active = BooleanField(default=True)
    credits = FloatField(default=0.0)
    created_at = DateTimeField(default=lambda: datetime.now(ist))
    updated_at = DateTimeField(default=lambda: datetime.now(ist))
    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'username'
        ],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(ist)
        return super(User, self).save(*args, **kwargs)


class RefreshToken(Document):
    user_id = StringField(required=True)
    token = StringField(required=True, unique=True)
    expires_at = DateTimeField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(ist))

    meta = {
        'collection': 'refresh_tokens',
        'indexes': [
            'token',
            'user_id',
            'expires_at'
        ],
        "db_alias": "kyc_fabric_db"
    }
