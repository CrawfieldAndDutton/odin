from datetime import datetime
import mongoengine as me
from pytz import timezone

# Define IST timezone
ist = timezone('Asia/Kolkata')


class User(me.Document):
    email = me.EmailField(required=True, unique=True)
    username = me.StringField(required=True, unique=True)
    hashed_password = me.StringField(required=True)
    first_name = me.StringField()
    last_name = me.StringField()
    role = me.StringField(default="user", choices=["user", "admin"])
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=lambda: datetime.now(ist))
    updated_at = me.DateTimeField(default=lambda: datetime.now(ist))

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


class RefreshToken(me.Document):
    user_id = me.StringField(required=True)
    token = me.StringField(required=True, unique=True)
    expires_at = me.DateTimeField(required=True)
    created_at = me.DateTimeField(default=lambda: datetime.now(ist))

    meta = {
        'collection': 'refresh_tokens',
        'indexes': [
            'token',
            'user_id',
            'expires_at'
        ],
        "db_alias": "kyc_fabric_db"
    }
