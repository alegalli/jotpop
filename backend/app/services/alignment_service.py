from datetime import date

from sqlalchemy.orm import Session

from app.models import Character, DailyPromise
from app.services.forge_service import (
    get_alignment_percent,
    get_completed_count,
    get_completed_forge_points,
    get_total_forge_points,
    is_forge_active_today,
)

ALIGNMENT_QUESTION = "Did you do what mattered?"


def get_alignment_label(alignment_percent: int, selected_count: int) -> str:
    if selected_count <= 0:
        return "Unchosen"
    if alignment_percent <= 0:
        return "Unstarted"
    if alignment_percent < 50:
        return "Misaligned"
    if alignment_percent < 80:
        return "Partly Aligned"
    if alignment_percent < 100:
        return "Aligned"
    return "Fully Aligned"


def get_alignment_message(alignment_percent: int, selected_count: int, forge_active_today: bool) -> str:
    if selected_count <= 0:
        return "Choose 3 Promises so Alignment can measure whether today matches what mattered."
    if alignment_percent <= 0:
        return "Your Promises are locked, but none have been forged yet."
    if alignment_percent < 50:
        return "You started, but most of today's Promise weight is still open."
    if alignment_percent < 80:
        if forge_active_today:
            return "You showed up enough to light the Forge, but Alignment says there is still meaningful weight left."
        return "You completed part of what mattered, but the day is not aligned yet."
    if alignment_percent < 100:
        return "Strong alignment. One more forged Promise can turn this into full alignment."
    return "Full alignment. You did all 3 selected Promises today."


def build_alignment_snapshot(
    character: Character,
    daily_promises: list[DailyPromise],
    selected_date: date | None = None,
) -> dict:
    day = selected_date or date.today()
    total_points = get_total_forge_points(daily_promises)
    completed_points = get_completed_forge_points(daily_promises)
    alignment_percent = get_alignment_percent(daily_promises)
    active_today = is_forge_active_today(daily_promises)
    selected_count = len(daily_promises)

    incomplete_promises = [promise for promise in daily_promises if promise.completion is None]
    incomplete_promises.sort(key=lambda promise: promise.forge_points, reverse=True)

    label = get_alignment_label(alignment_percent, selected_count)
    message = get_alignment_message(alignment_percent, selected_count, active_today)

    return {
        "selected_date": day,
        "question": ALIGNMENT_QUESTION,
        "alignment_percent": alignment_percent,
        "alignment_label": label,
        "alignment_message": message,
        "selected_count": selected_count,
        "completed_count": get_completed_count(daily_promises),
        "total_forge_points": total_points,
        "completed_forge_points": completed_points,
        "remaining_forge_points": max(0, total_points - completed_points),
        "forge_active_today": active_today,
        "forge_state": character.forge_state or "Cold",
        "forge_days": character.forge_days or 0,
        "incomplete_promises": incomplete_promises,
        "note": "Forge answers: Did you show up? Alignment answers: Did you do what mattered?",
    }


def sync_today_alignment(db: Session, character: Character, daily_promises: list[DailyPromise]) -> int:
    alignment_percent = get_alignment_percent(daily_promises)
    if character.today_alignment != alignment_percent:
        character.today_alignment = alignment_percent
        db.commit()
        db.refresh(character)
    return alignment_percent
