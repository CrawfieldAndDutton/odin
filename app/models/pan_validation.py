import mongoengine as me
from datetime import datetime


class PANValidationResult(me.Document):
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    txn_id = me.StringField(required=True, unique=True)
    pan = me.StringField(required=True)
    status = me.StringField()
    message = me.StringField()
    status_code = me.IntField()
    pan_status = me.StringField()
    pan_type = me.StringField()
    full_name = me.StringField()

    meta = {
        'collection': 'pan_validation_results',
        'indexes': [
            'txn_id',
            'pan',
            'created_at'
        ]
    }
