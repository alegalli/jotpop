from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Character, User
from app.routers.auth import get_current_user
from app.schemas.insight import (
    InsightListResponse,
    InsightRespondRequest,
    InsightRespondResponse,
    InsightResponse,
    InsightStatusResponse,
)
from app.services.auth_service import get_active_character
from app.services.insight_service import (
    get_insight_status,
    list_insights_for_character,
    respond_to_insight,
)

router = APIRouter(prefix="/insights", tags=["insights"])


def get_current_character(current_user: User) -> Character:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active character not found",
        )
    return character


@router.get("/status", response_model=InsightStatusResponse)
def insight_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InsightStatusResponse:
    character = get_current_character(current_user)
    return InsightStatusResponse(**get_insight_status(db, character))


@router.get("", response_model=InsightListResponse)
def list_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InsightListResponse:
    character = get_current_character(current_user)
    insights = list_insights_for_character(db, character)
    return InsightListResponse(status="ok", insights=insights)


@router.post("/{insight_id}/respond", response_model=InsightRespondResponse)
def respond_insight(
    insight_id: int,
    payload: InsightRespondRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InsightRespondResponse:
    character = get_current_character(current_user)
    insight = respond_to_insight(db, character, insight_id, payload.accepted)
    if insight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found",
        )

    message = "Insight accepted. The pattern grows stronger." if payload.accepted else "Insight rejected. The system will treat this pattern as weaker."
    return InsightRespondResponse(
        status="ok",
        insight=InsightResponse.model_validate(insight),
        message=message,
    )
