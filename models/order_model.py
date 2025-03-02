from mongoengine import Document,  DateTimeField, IntField
from mongoengine import DictField, StringField
from datetime import datetime


class PANValidationResult(Document):
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    txn_id = StringField(unique=True)
    pan = StringField(required=True)
    status = StringField()
    message = StringField()
    status_code = IntField()
    pan_status = StringField()
    pan_type = StringField()
    full_name = StringField()
    raw_response = DictField()
    user_id = StringField()
    meta = {
        'collection': 'pan_validation_provider_responses',
        'indexes': [
            'txn_id',
            'pan',
            'created_at',
            'user_id'
        ],
        "db_alias": "kyc_fabric_db"
    }


class PanVerificationLog(Document):
    pan = StringField(required=True)
    user_id = StringField()
    ip_address = StringField()
    user_agent = StringField()
    timestamp = DateTimeField(default=datetime.now)
    pan_validation_provider_response_id = StringField()
    updated_at = DateTimeField(default=datetime.now)
    # Whether data came from DB or external API
    source = StringField(choices=["db", "api"])
    meta = {
        'collection': 'pan_validation_transactions',
        'indexes': [
            'pan',
            'timestamp',
            'user_id'
        ],
        "db_alias": "kyc_fabric_db"
    }


class VehicleRecord(Document):
    reg_no = StringField(required=True, unique=True)
    state = StringField()
    owner_name = StringField()
    vehicle_manufacturer = StringField()
    model = StringField()
    registration_date = DateTimeField()
    registration_valid_upto = DateTimeField()
    insurance_valid_upto = DateTimeField()
    pucc_valid_upto = DateTimeField()
    raw_response = DictField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    user_id = StringField()
    meta = {
        'collection': 'vehicle_validation_provider_responses',
        'indexes': ['reg_no',
                    'created_at',
                    'user_id'
                    ],
        "db_alias": "kyc_fabric_db"
    }


class VehicleVerificationLog(Document):
    reg_no = StringField(required=True)
    user_id = StringField()
    ip_address = StringField()
    user_agent = StringField()
    timestamp = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    vehicle_validation_provider_response_id = StringField()
    # Whether data came from DB or external API
    source = StringField(choices=["db", "api"])
    meta = {
        'collection': 'vehicle_validation_transactions',
        'indexes': [
            'reg_no',
            'timestamp',
            'user_id'
        ],
        "db_alias": "kyc_fabric_db"
    }
