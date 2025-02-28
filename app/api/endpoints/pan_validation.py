from fastapi import APIRouter
from app.schemas.pan_validation import (
    PANValidationRequest,
    PANValidationResponse,
    PANHistoryResponse
)
from app.services.pan_validation_service import PANValidationService
router = APIRouter()
@router.post("/validate-pan", response_model=PANValidationResponse)
async def validate_pan(request: PANValidationRequest):
    """
    Validates a PAN number through external API and stores the result in the database
    """
    # Check if we already have this PAN in our database (recent result)
    cached_result = await PANValidationService.get_cached_validation(request.pan)
    if cached_result:
        return cached_result
    # Call external API
    result = await PANValidationService.call_external_api(request.pan)
    # Save result to database
    PANValidationService.save_validation_result(request.pan, result)
    return result
@router.get("/pan-history/{pan}", response_model=PANHistoryResponse)
async def get_pan_history(pan: str):
    """
    Get validation history for a specific PAN
    """
    history = await PANValidationService.get_pan_history(pan)
    if not history:
        return {"history": []}
    return {"history": history}