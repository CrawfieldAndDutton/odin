# Standard library imports
from datetime import datetime
# from typing import Optional

# Third-party library imports
from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField,
    ReferenceField,
    IntField,
)
from pytz import timezone

# Local application imports
from models.user_model import User

# Define IST timezone
ist = timezone('Asia/Kolkata')


class Order(Document):
    """
    Model for storing order information related to payment links.
    """
    order_id = StringField(required=True, unique=True)
    user = ReferenceField(User, required=True)
    amount = FloatField(required=True)
    currency = StringField(required=True, default="INR")
    status = StringField(required=True, default="pending", choices=["pending", "paid", "failed", "cancelled"])
    short_url = StringField()
    credits_purchased = IntField(required=True)
    razorpay_payment_link_id = StringField()
    created_at = DateTimeField(default=lambda: datetime.now(ist))
    updated_at = DateTimeField(default=lambda: datetime.now(ist))

    meta = {
        'collection': 'orders',
        'indexes': [
            'order_id',
            'user',
            'status',
            'created_at'
        ],
        'db_alias': 'kyc_fabric_db'
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(ist)
        return super(Order, self).save(*args, **kwargs)


class Payment(Document):
    """
    Model for storing payment information after payment is processed.
    """
    order = ReferenceField(Order, required=True)
    payment_id = StringField(required=True, unique=True)
    user = ReferenceField(User, required=True)
    amount = FloatField(required=True)
    currency = StringField(required=True, default="INR")
    payment_method = StringField()
    status = StringField(required=True, choices=["created", "authorized", "captured", "refunded", "failed"])
    signature = StringField()
    created_at = DateTimeField(default=lambda: datetime.now(ist))
    updated_at = DateTimeField(default=lambda: datetime.now(ist))

    meta = {
        'collection': 'payments',
        'indexes': [
            'payment_id',
            'order',
            'user',
            'status',
            'created_at'
        ],
        'db_alias': 'kyc_fabric_db'
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(ist)
        return super(Payment, self).save(*args, **kwargs)
