# Standard library imports
from datetime import datetime

# Third-party library imports
from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField,
    DictField,
)

# Local application imports
from dependencies.constants import IST


class PaymentTransaction(Document):
    """
    Combined model for storing all payment-related information in a single document.
    This includes payment link creation, payment verification, and webhook responses.
    """
    user_id = StringField(required=True)
    total_amount = FloatField(required=True)
    currency = StringField(required=True, default="INR")
    credits_purchased = FloatField(required=True)
    order_id = StringField()
    order_status = StringField(required=True, default="pending",
                               choices=["pending", "paid", "failed", "cancelled"])
    payment_status = StringField(required=True, default="pending",
                                 choices=["pending", "created", "authorized",
                                          "captured", "refunded", "failed", "cancelled"])
    payment_id = StringField()
    payment_method = StringField()
    short_url = StringField()
    razorpay_payment_link_id = StringField()
    razorpay_response = DictField()  # Response from Razorpay when creating payment link
    payment_response_from_razorpay = DictField()  # Response from Razorpay after payment
    webhook_responses = DictField()  # Responses from Razorpay webhooks
    signature = StringField()  # Payment verification signature
    created_at = DateTimeField(default=datetime.now(IST))
    updated_at = DateTimeField(default=datetime.now(IST))

    meta = {
        'collection': 'payment_transactions',
        'indexes': [
            'user_id',
            'order_id',
            'payment_id',
            'razorpay_payment_link_id',
            'order_status',
            'payment_status',
            'created_at'
        ],
        'ordering': ['-created_at'],
        "db_alias": "kyc_fabric_db"
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(IST)
        return super(PaymentTransaction, self).save(*args, **kwargs)
