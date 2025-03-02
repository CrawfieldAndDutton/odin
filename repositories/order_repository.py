from models.order_model import PANValidationResult, PanVerificationLog
from models.order_model import VehicleRecord, VehicleVerificationLog
from dependencies.utils import format_date


class PanRepository:
    @staticmethod
    def find_pan_by_pan_no(pan: str):
        """Find a vehicle record by registration number."""
        return PANValidationResult.objects(pan=pan).first()

    @staticmethod
    def create_pan_record(data: dict):
        """Create a new vehicle record."""
        pan_record = PANValidationResult(**data)
        pan_record.save()
        return pan_record

    @staticmethod
    def log_verification_attempt(data: dict):
        """Log a verification attempt."""
        log_entry = PanVerificationLog(**data)
        log_entry.save()
        return log_entry

    @staticmethod
    def pan_to_dict(pan: PANValidationResult):
        """Convert a panRecord to a dictionary."""
        if not pan:
            return None

        return {
            "txn_id": pan.txn_id,
            "pan": pan.pan,
            "status": pan.status,
            "message": pan.message,
            "status_code": pan.status_code,
            "result": {
                "pan_status": pan.pan_status,
                "pan_type": pan.pan_type,
                "pan": pan.pan,
                "full_name": pan.full_name
            },
            "raw_response": pan.raw_response
        }


class VehicleRepository:
    @staticmethod
    def find_vehicle_by_reg_no(reg_no: str):
        """Find a vehicle record by registration number."""
        return VehicleRecord.objects(reg_no=reg_no).first()

    @staticmethod
    def create_vehicle_record(data: dict):
        """Create a new vehicle record."""
        vehicle_record = VehicleRecord(**data)
        vehicle_record.save()
        return vehicle_record

    @staticmethod
    def log_verification_attempt(data: dict):
        """Log a verification attempt."""
        log_entry = VehicleVerificationLog(**data)
        log_entry.save()
        return log_entry

    @staticmethod
    def vehicle_to_dict(vehicle: VehicleRecord):
        """Convert a VehicleRecord to a dictionary."""
        if not vehicle:
            return None

        return {
            "status": "success",
            "reg_no": vehicle.reg_no,
            "state": vehicle.state,
            "owner_name": vehicle.owner_name,
            "vehicle_manufacturer": vehicle.vehicle_manufacturer,
            "model": vehicle.model,
            "registration_date": format_date(vehicle.registration_date),
            "registration_valid_upto": format_date(vehicle.registration_valid_upto),
            "insurance_valid_upto": format_date(vehicle.insurance_valid_upto),
            "pucc_valid_upto": format_date(vehicle.pucc_valid_upto),
            "raw_response": vehicle.raw_response
        }
