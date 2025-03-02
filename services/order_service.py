import requests
from fastapi import HTTPException, status
from dependencies.config import Config
from repositories.order_repository import PanRepository, VehicleRepository
from dependencies.utils import parse_date


class PanService:
    def __init__(self):
        self.api_key = Config.RAPID_API_KEY
        self.api_url = Config.PAN_API_URL
        self.repository = PanRepository()

    def log_verification(self, pan, client_info, source, pan_validation_provider_response_id):
        """Log verification attempt."""
        log_data = {
            "pan": pan,
            "ip_address": client_info.get("ip"),
            "user_agent": client_info.get("user_agent"),
            "source": source,
            "pan_validation_provider_response_id": pan_validation_provider_response_id
        }
        if client_info.get("user_id"):
            log_data["user_id"] = client_info.get("user_id")

        return self.repository.log_verification_attempt(log_data)

    def get_pan_from_db(self, pan, client_info=None):
        """Get vehicle data from database."""
        panDetails = self.repository.find_pan_by_pan_no(pan)

        if panDetails and client_info:
            if "user_id" not in client_info:
                client_info["user_id"] = None
            self.log_verification(pan, client_info, "db",
                                  str(panDetails.id))

        return self.repository.pan_to_dict(panDetails)

    def fetch_pan_from_api(self, pan):
        """Fetch vehicle data from external API."""
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-key": self.api_key
        }

        payload = {
            "pan": pan,
            "consent": "yes",
            "consent_text": "I hear by declare my consent agreement for fetching my information via AITAN Labs API"
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch pan data: {str(e)}"
            )

    def extract_pan_info(self, api_response):
        """Extract relevant vehicle information from API response."""
        if api_response.get("status") != "success":
            return {
                "status": "error",
                "message": api_response.get("message", "Failed to retrieve pan information")
            }

        result = api_response.get("result", {})

        pan_info = {
            "status": api_response.get("status"),
            "status_code": api_response.get("status_code"),
            "pan": result.get("pan"),
            "message": api_response.get("message"),
            "pan_status": result.get("pan_status"),
            "txn_id": api_response.get("txn_id"),
            "full_name": result.get("full_name"),
            "pan_type": result.get("pan_type"),
            "result": {  # Map the result field
                "pan_status": result.get("pan_status"),
                "pan_type": result.get("pan_type"),
                "pan": result.get("pan"),
                "full_name": result.get("full_name")
            }
        }
        return pan_info

    def verify_pan(self, pan, client_info=None, pan_validation_provider_response_id=None):
        """
        Verify vehicle details using the registration number.
        """
        pan = pan.upper().strip()

        # Check database first
        pan_data = self.get_pan_from_db(pan, client_info)
        if pan_data:
            return pan_data

        # Call external API if not in database
        api_response = self.fetch_pan_from_api(pan)
        pan_info = self.extract_pan_info(api_response)

        if pan_info.get("status") == "error":
            return {
                "status": "error",
                "pan": pan,
                "message": pan_info.get("message")
            }

        # Save to database
        pan_data = {
            "status": pan_info.get("status"),
            "status_code": pan_info.get("status_code"),
            "pan": pan_info.get("pan"),
            "message": pan_info.get("message"),
            "pan_status": pan_info.get("pan_status"),
            "txn_id": pan_info.get("txn_id"),
            "full_name": pan_info.get("full_name"),
            "pan_type": pan_info.get("pan_type"),
            "raw_response": api_response,
            "user_id": client_info.get("user_id")
        }

    # Create PANValidationResult document and save it
        pan_record = self.repository.create_pan_record(pan_data)

    # Log the API verification with the PANValidationResult _id
        if client_info:
            self.log_verification(pan, client_info, "api", str(pan_record.id))
        # Add raw_response to vehicle_info
        pan_info["raw_response"] = api_response

        return pan_info


class VehicleService:
    def __init__(self):
        self.api_key = Config.RAPID_API_KEY
        self.api_url = Config.VEHICLE_API_URL
        self.repository = VehicleRepository()

    def log_verification(self, reg_no, client_info, source, vehicle_validation_provider_response_id):
        """Log verification attempt."""
        log_data = {
            "reg_no": reg_no,
            "ip_address": client_info.get("ip"),
            "user_agent": client_info.get("user_agent"),
            "source": source,
            "vehicle_validation_provider_response_id": vehicle_validation_provider_response_id
        }
        if client_info.get("user_id"):
            log_data["user_id"] = client_info.get("user_id")

        return self.repository.log_verification_attempt(log_data)

    def get_vehicle_from_db(self, reg_no, client_info=None):
        """Get vehicle data from database."""
        vehicle = self.repository.find_vehicle_by_reg_no(reg_no)

        if vehicle and client_info:
            self.log_verification(reg_no, client_info, "db", str(vehicle.id))

        return self.repository.vehicle_to_dict(vehicle)

    def fetch_vehicle_from_api(self, reg_no):
        """Fetch vehicle data from external API."""
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-key": self.api_key
        }

        payload = {
            "reg_no": reg_no,
            "consent": "yes",
            "consent_text": "I hear by declare my consent agreement for fetching my information via AITAN Labs API"
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch vehicle data: {str(e)}"
            )

    def extract_vehicle_info(self, api_response):
        """Extract relevant vehicle information from API response."""
        if api_response.get("status") != "success":
            return {
                "status": "error",
                "message": api_response.get("message", "Failed to retrieve vehicle information")
            }

        result = api_response.get("result", {})

        vehicle_info = {
            "status": "success",
            "reg_no": result.get("reg_no"),
            "state": result.get("state"),
            "owner_name": result.get("owner_name"),
            "vehicle_manufacturer": result.get("vehicle_manufacturer_name"),
            "model": result.get("model"),
            "registration_date": result.get("reg_date"),
            "registration_valid_upto": result.get("reg_upto"),
        }

        # Extract insurance details if available
        insurance_details = result.get("vehicle_insurance_details", {})
        if insurance_details:
            vehicle_info["insurance_valid_upto"] = insurance_details.get(
                "insurance_upto")

        # Extract PUCC details if available
        pucc_details = result.get("vehicle_pucc_details", {})
        if pucc_details:
            vehicle_info["pucc_valid_upto"] = pucc_details.get("pucc_upto")

        return vehicle_info

    def verify_vehicle(self, reg_no, client_info=None, vehicle_validation_provider_response_id=None):
        """
        Verify vehicle details using the registration number.
        """
        reg_no = reg_no.upper().strip()

        # Check database first
        vehicle_data = self.get_vehicle_from_db(reg_no, client_info)
        if vehicle_data:
            return vehicle_data

        # Call external API if not in database
        api_response = self.fetch_vehicle_from_api(reg_no)
        vehicle_info = self.extract_vehicle_info(api_response)

        if vehicle_info.get("status") == "error":
            return {
                "status": "error",
                "reg_no": reg_no,
                "message": vehicle_info.get("message")
            }

        # Log the API verification
        # if client_info:
        #     self.log_verification(reg_no, client_info, "api",
        #                           vehicle_validation_provider_response_id)

        # Save to database
        vehicle_data = {
            "reg_no": vehicle_info.get("reg_no"),
            "state": vehicle_info.get("state"),
            "owner_name": vehicle_info.get("owner_name"),
            "vehicle_manufacturer": vehicle_info.get("vehicle_manufacturer"),
            "model": vehicle_info.get("model"),
            "registration_date": parse_date(vehicle_info.get("registration_date")),
            "registration_valid_upto": parse_date(vehicle_info.get("registration_valid_upto")),
            "insurance_valid_upto": parse_date(vehicle_info.get("insurance_valid_upto")),
            "pucc_valid_upto": parse_date(vehicle_info.get("pucc_valid_upto")),
            "raw_response": api_response,
            "user_id": client_info.get("user_id")
        }

        vehicle_record = self.repository.create_vehicle_record(vehicle_data)

        # Log the API verification with the vehicleValidationResult _id
        if client_info:
            self.log_verification(reg_no, client_info,
                                  "api", str(vehicle_record.id))

        # Add raw_response to vehicle_info
        vehicle_info["raw_response"] = api_response

        return vehicle_info
