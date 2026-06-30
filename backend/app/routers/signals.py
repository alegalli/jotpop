from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Character, User
from app.routers.auth import get_current_user
from app.schemas.signal import (
    CardSignalCreateRequest,
    SignalCreateResponse,
    SignalImportRequest,
    SignalImportResponse,
    SignalResponse,
    SignalSummaryResponse,
)
from app.schemas.user import CharacterResponse
from app.services.auth_service import get_active_character
from app.services.signal_service import (
    create_card_signal_for_character,
    get_latest_signals_for_character,
    import_onboarding_signals_for_character,
)

router = APIRouter(prefix="/signals", tags=["signals"])


def get_current_character(current_user: User) -> Character:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active character not found",
        )
    return character


@router.post("/import-onboarding", response_model=SignalImportResponse)
def import_onboarding_signals(
    payload: SignalImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SignalImportResponse:
    character = get_current_character(current_user)

    imported, skipped, accepted_imported = import_onboarding_signals_for_character(
        db=db,
        character=character,
        payload=payload,
    )

    return SignalImportResponse(
        status="ok",
        imported=imported,
        skipped=skipped,
        accepted_imported=accepted_imported,
        total_signal_count=character.total_signal_count,
        accepted_signal_count=character.accepted_signal_count,
        character=CharacterResponse.model_validate(character),
    )


@router.post("/card", response_model=SignalCreateResponse, status_code=status.HTTP_201_CREATED)
def create_card_signal(
    payload: CardSignalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SignalCreateResponse:
    character = get_current_character(current_user)
    signal = create_card_signal_for_character(
        db=db,
        character=character,
        payload=payload,
    )

    return SignalCreateResponse(
        status="ok",
        signal=SignalResponse.model_validate(signal),
        total_signal_count=character.total_signal_count,
        accepted_signal_count=character.accepted_signal_count,
        character=CharacterResponse.model_validate(character),
    )


@router.get("/summary", response_model=SignalSummaryResponse)
def signal_summary(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SignalSummaryResponse:
    character = get_current_character(current_user)
    latest_signals = get_latest_signals_for_character(db, character, limit=limit)

    return SignalSummaryResponse(
        status="ok",
        total_signal_count=character.total_signal_count,
        accepted_signal_count=character.accepted_signal_count,
        latest_signals=latest_signals,
    )
