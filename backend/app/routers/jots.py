from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Character, User
from app.routers.auth import get_current_user
from app.schemas.jot import JotCreateRequest, JotCreateResponse, JotResponse, JotSummaryResponse
from app.services.auth_service import get_active_character
from app.services.jot_service import (
    clean_jot_content,
    create_manual_jot_for_character,
    get_jot_path_message,
    get_latest_jots_for_character,
    get_total_jots_for_character,
)

router = APIRouter(prefix="/jots", tags=["jots"])


def get_current_character(current_user: User) -> Character:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active character not found",
        )
    return character


@router.get("/summary", response_model=JotSummaryResponse)
def jot_summary(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JotSummaryResponse:
    character = get_current_character(current_user)
    total_jots = get_total_jots_for_character(db, character)
    latest_jots = get_latest_jots_for_character(db, character, limit=limit)

    return JotSummaryResponse(
        status="ok",
        total_jots=total_jots,
        latest_jots=[JotResponse.model_validate(jot) for jot in latest_jots],
        path_message=get_jot_path_message(total_jots),
    )


@router.post("", response_model=JotCreateResponse, status_code=status.HTTP_201_CREATED)
def create_jot(
    payload: JotCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JotCreateResponse:
    character = get_current_character(current_user)
    content = clean_jot_content(payload.content)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Write a Jot first.",
        )
    if len(content) > 140:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Jot must be 140 characters or fewer.",
        )

    jot = create_manual_jot_for_character(
        db=db,
        character=character,
        content=content,
        prompt=payload.prompt,
    )
    total_jots = get_total_jots_for_character(db, character)

    return JotCreateResponse(
        status="ok",
        jot=JotResponse.model_validate(jot),
        total_jots=total_jots,
        path_message=get_jot_path_message(total_jots),
    )
