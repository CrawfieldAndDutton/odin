import mongoengine as me
from datetime import datetime


class User(me.Document):
    email = me.EmailField(required=True, unique=True)
    username = me.StringField(required=True, unique=True)
    hashed_password = me.StringField(required=True)
    first_name = me.StringField()
    last_name = me.StringField()
    # Added role field with default "user"
    role = me.StringField(default="user", choices=["user", "admin"])
    is_active = me.BooleanField(default=True)
    is_superuser = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(
        default=datetime.utcnow)  # Added updated_at field

    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'username'
        ],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        # Update the updated_at field on every save
        self.updated_at = datetime.utcnow()
        return super(User, self).save(*args, **kwargs)


class RefreshToken(me.Document):
    user_id = me.StringField(required=True)
    token = me.StringField(required=True, unique=True)
    expires_at = me.DateTimeField(required=True)
    revoked = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'refresh_tokens',
        'indexes': [
            'token',
            'user_id',
            'expires_at'
        ],
        "db_alias": "kyc_fabric_db"
    }
