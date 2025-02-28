import httpx
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.pan_validation import PANValidationResult
from app.config import settings
from fastapi import HTTPException


class PANValidationService:
    @staticmethod
    async def get_cached_validation(pan: str) -> Optional[Dict[str, Any]]:
        """Get cached validation result if it exists for today"""
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0)
        existing_result = PANValidationResult._get_collection().find_one({
            'pan': pan,
            'created_at': {'$gte': today_start}
        })

        if existing_result:
            # Convert ObjectId to string for JSON serialization
            existing_result["_id"] = str(existing_result["_id"])
            return {
                "txn_id": existing_result.get("txn_id"),
                "status": existing_result.get("status"),
                "message": existing_result.get("message"),
                "status_code": existing_result.get("status_code"),
                "result": {
                    "pan_status": existing_result.get("pan_status"),
                    "pan_type": existing_result.get("pan_type"),
                    "pan": existing_result.get("pan"),
                    "full_name": existing_result.get("full_name")
                }
            }
        return None

    @staticmethod
    async def call_external_api(pan: str) -> Dict[str, Any]:
        """Call the external API to validate PAN"""
        payload = {
            "pan": pan,
            "consent": "yes",
            "consent_text": "I hear by declare my consent agreement for fetching my information via AITAN Labs API"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.PAN_VALIDATION_API_URL,
                    json=payload,
                    headers=settings.PAN_API_HEADERS
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail=f"API Error: {response.text}")

            return response.json()

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f"Error calling external API: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}")

    @staticmethod
    def save_validation_result(pan: str, result: Dict[str, Any]) -> None:
        """Save validation result to database"""
        result_data = result.get("result", {})

        validation_result = PANValidationResult(
            txn_id=result.get("txn_id", str(uuid.uuid4())),
            pan=pan,
            status=result.get("status"),
            message=result.get("message"),
            status_code=result.get("status_code"),
            pan_status=result_data.get("pan_status"),
            pan_type=result_data.get("pan_type"),
            full_name=result_data.get("full_name")
        )
        validation_result.save()

    @staticmethod
    async def get_pan_history(pan: str) -> List[Dict[str, Any]]:
        """Get validation history for a specific PAN"""
        results = list(PANValidationResult._get_collection().find(
            {'pan': pan}
        ).sort('created_at', -1))

        history = []
        for result in results:
            # Convert ObjectId to string
            result["_id"] = str(result["_id"])

            # Convert datetime objects to ISO format strings
            if isinstance(result.get("created_at"), datetime):
                result["created_at"] = result["created_at"].isoformat()
            if isinstance(result.get("updated_at"), datetime):
                result["updated_at"] = result["updated_at"].isoformat()

            history.append({
                "txn_id": result.get("txn_id"),
                "status": result.get("status"),
                "message": result.get("message"),
                "status_code": result.get("status_code"),
                "pan_status": result.get("pan_status"),
                "pan_type": result.get("pan_type"),
                "pan": result.get("pan"),
                "full_name": result.get("full_name"),
                "created_at": result.get("created_at")
            })

        return history
