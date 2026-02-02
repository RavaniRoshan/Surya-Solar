from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.api.dependencies import get_current_user
from app.core.auth import TokenData

router = APIRouter(prefix="/feedback", tags=["Feedback"])

class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comments: str
    feature_feedback: Optional[str] = None

@router.post("/", status_code=201)
async def submit_feedback(
    feedback: FeedbackCreate,
    user: TokenData = Depends(get_current_user)
):
    """
    Submit beta feedback.
    """
    # In production, save to database
    # For now, we return success to confirm receipt
    return {"status": "success", "message": "Feedback received", "data": feedback}
