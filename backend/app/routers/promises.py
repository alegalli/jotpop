from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.schemas.promise import (
    AlignmentStatusResponse,
    DailyPromiseResponse,
    ForgeStatusResponse,
    PromiseForgeRequest,
    PromiseForgeResponse,
    PromiseSelectionRequest,
    PromiseSelectionResponse,
    PromiseStatsResponse,
    PromiseSuggestionResponse,
    PromiseTemplateListResponse,
    PromiseTemplateResponse,
    TodayPromisesResponse,
)
from app.services.alignment_service import build_alignment_snapshot, sync_today_alignment
from app.services.auth_service import get_active_character
from app.services.forge_service import build_forge_snapshot, sync_today_forge_state_if_needed
from app.services.promise_service import (
    REQUIRED_DAILY_PROMISE_COUNT,
    complete_daily_promise,
    daily_promise_to_response_data,
    get_active_promise_templates,
    get_alignment_percent,
    get_completed_count,
    get_completed_forge_points,
    get_promise_template_stats,
    get_today_daily_promises,
    get_today_forge_snapshot,
    get_today_promise_suggestions,
    get_total_forge_points,
    select_today_promises,
)

router = APIRouter(prefix="/promises", tags=["promises"])


def build_daily_promise_responses(daily_promises) -> list[DailyPromiseResponse]:
    return [DailyPromiseResponse(**daily_promise_to_response_data(promise)) for promise in daily_promises]


def build_today_promises_response(character, daily_promises, selected_date: date | None = None) -> TodayPromisesResponse:
    day = selected_date or date.today()
    forge_snapshot = build_forge_snapshot(character, daily_promises)
    alignment_snapshot = build_alignment_snapshot(character, daily_promises, day)
    return TodayPromisesResponse(
        status="ok",
        selected_date=day,
        required_selection_count=REQUIRED_DAILY_PROMISE_COUNT,
        selected_count=len(daily_promises),
        completed_count=get_completed_count(daily_promises),
        is_locked=len(daily_promises) >= REQUIRED_DAILY_PROMISE_COUNT,
        total_forge_points=get_total_forge_points(daily_promises),
        completed_forge_points=get_completed_forge_points(daily_promises),
        alignment_percent=alignment_snapshot["alignment_percent"],
        alignment_label=alignment_snapshot["alignment_label"],
        alignment_message=alignment_snapshot["alignment_message"],
        remaining_forge_points=alignment_snapshot["remaining_forge_points"],
        alignment_question=alignment_snapshot["question"],
        forge_threshold_points=forge_snapshot["forge_threshold_points"],
        forge_active_today=forge_snapshot["forge_active_today"],
        forge_points_needed_today=forge_snapshot["forge_points_needed_today"],
        forge_days=forge_snapshot["forge_days"],
        forge_state=forge_snapshot["forge_state"],
        forge_cooling=forge_snapshot["forge_cooling"],
        daily_promises=build_daily_promise_responses(daily_promises),
    )


@router.get("/templates", response_model=PromiseTemplateListResponse)
def list_promise_templates(db: Session = Depends(get_db)) -> PromiseTemplateListResponse:
    templates = get_active_promise_templates(db)
    return PromiseTemplateListResponse(
        status="ok",
        count=len(templates),
        templates=[PromiseTemplateResponse.model_validate(template) for template in templates],
    )


@router.get("/suggestions/today", response_model=PromiseSuggestionResponse)
def today_promise_suggestions(
    limit: int = Query(default=7, ge=1, le=12),
    db: Session = Depends(get_db),
) -> PromiseSuggestionResponse:
    suggestions = get_today_promise_suggestions(db, limit=limit)
    return PromiseSuggestionResponse(
        status="ok",
        count=len(suggestions),
        required_selection_count=REQUIRED_DAILY_PROMISE_COUNT,
        note="Choose exactly 3. Once selected, today's Promises are locked.",
        suggestions=[PromiseTemplateResponse.model_validate(template) for template in suggestions],
    )


@router.get("/today", response_model=TodayPromisesResponse)
def get_today_promises(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TodayPromisesResponse:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active character not found")

    daily_promises = get_today_daily_promises(db, character.id)
    sync_today_forge_state_if_needed(db, character, daily_promises)
    sync_today_alignment(db, character, daily_promises)
    return build_today_promises_response(character, daily_promises)


@router.get("/forge-status", response_model=ForgeStatusResponse)
def get_forge_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForgeStatusResponse:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active character not found")

    snapshot = get_today_forge_snapshot(db, character)
    return ForgeStatusResponse(
        status="ok",
        note="Forge is active today once completed selected Promise points reach 2 or more.",
        **snapshot,
    )


@router.get("/alignment-status", response_model=AlignmentStatusResponse)
def get_alignment_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlignmentStatusResponse:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active character not found")

    daily_promises = get_today_daily_promises(db, character.id)
    sync_today_forge_state_if_needed(db, character, daily_promises)
    sync_today_alignment(db, character, daily_promises)
    snapshot = build_alignment_snapshot(character, daily_promises)

    return AlignmentStatusResponse(
        status="ok",
        selected_date=snapshot["selected_date"],
        question=snapshot["question"],
        alignment_percent=snapshot["alignment_percent"],
        alignment_label=snapshot["alignment_label"],
        alignment_message=snapshot["alignment_message"],
        selected_count=snapshot["selected_count"],
        completed_count=snapshot["completed_count"],
        total_forge_points=snapshot["total_forge_points"],
        completed_forge_points=snapshot["completed_forge_points"],
        remaining_forge_points=snapshot["remaining_forge_points"],
        forge_active_today=snapshot["forge_active_today"],
        forge_state=snapshot["forge_state"],
        forge_days=snapshot["forge_days"],
        incomplete_promises=build_daily_promise_responses(snapshot["incomplete_promises"]),
        note=snapshot["note"],
    )


@router.post("/select-today", response_model=PromiseSelectionResponse, status_code=status.HTTP_201_CREATED)
def select_promises_for_today(
    payload: PromiseSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PromiseSelectionResponse:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active character not found")

    try:
        daily_promises = select_today_promises(db, character, payload.template_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    today = build_today_promises_response(character, daily_promises)
    return PromiseSelectionResponse(
        status="ok",
        message="Today's 3 Promises are locked.",
        selected_date=today.selected_date,
        required_selection_count=today.required_selection_count,
        selected_count=today.selected_count,
        completed_count=today.completed_count,
        is_locked=today.is_locked,
        total_forge_points=today.total_forge_points,
        completed_forge_points=today.completed_forge_points,
        alignment_percent=today.alignment_percent,
        alignment_label=today.alignment_label,
        alignment_message=today.alignment_message,
        remaining_forge_points=today.remaining_forge_points,
        alignment_question=today.alignment_question,
        forge_threshold_points=today.forge_threshold_points,
        forge_active_today=today.forge_active_today,
        forge_points_needed_today=today.forge_points_needed_today,
        forge_days=today.forge_days,
        forge_state=today.forge_state,
        forge_cooling=today.forge_cooling,
        daily_promises=today.daily_promises,
    )


@router.post("/{daily_promise_id}/forge", response_model=PromiseForgeResponse, status_code=status.HTTP_201_CREATED)
def forge_daily_promise(
    daily_promise_id: int,
    payload: PromiseForgeRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PromiseForgeResponse:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active character not found")

    try:
        forged_promise, threshold_crossed_now = complete_daily_promise(
            db=db,
            character=character,
            daily_promise_id=daily_promise_id,
            proof_text=payload.proof_text if payload else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    daily_promises = get_today_daily_promises(db, character.id)
    today = build_today_promises_response(character, daily_promises)

    if threshold_crossed_now:
        message = f"🔥 Forge {today.forge_state}. The Forge remembers."
    else:
        message = "🔥 Promise Forged. The Forge remembers."

    return PromiseForgeResponse(
        status="ok",
        message=message,
        forged_promise=DailyPromiseResponse(**daily_promise_to_response_data(forged_promise)),
        today=today,
    )


@router.get("/stats", response_model=PromiseStatsResponse)
def promise_stats(db: Session = Depends(get_db)) -> PromiseStatsResponse:
    stats = get_promise_template_stats(db)
    return PromiseStatsResponse(
        status="ok" if stats["active_templates"] >= 7 else "missing_templates",
        total_templates=stats["total_templates"],
        active_templates=stats["active_templates"],
        expected_minimum_templates=7,
        templates_ready=stats["active_templates"] >= 7,
        difficulty_counts=stats["difficulty_counts"],
    )
