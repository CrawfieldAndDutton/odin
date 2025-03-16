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

# Local application imports
from dependencies.constants import IST


class User(Document):
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    phone_number = StringField(required=True)
    hashed_password = StringField(required=True)
    first_name = StringField()
    last_name = StringField()
    role = StringField(default="user", choices=["user", "admin"])
    is_active = BooleanField(default=True)
    credits = FloatField(default=10.0)  # Free credits for the user for promotional purposes need to be removed later
    created_at = DateTimeField(default=lambda: datetime.now(IST))
    updated_at = DateTimeField(default=lambda: datetime.now(IST))

    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'username'
        ],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(IST)
        return super(User, self).save(*args, **kwargs)


class RefreshToken(Document):
    user_id = StringField(required=True)
    token = StringField(required=True, unique=True)
    expires_at = DateTimeField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(IST))

    meta = {
        'collection': 'refresh_tokens',
        'indexes': [
            'token',
            'user_id',
            'expires_at'
        ],
        "db_alias": "kyc_fabric_db"
    }


class VerifiedUserInformation(Document):
    phone_number = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    otp = StringField()
    is_verified = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)
