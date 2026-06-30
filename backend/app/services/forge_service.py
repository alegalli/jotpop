from datetime import date

from sqlalchemy.orm import Session

from app.models import Character, DailyPromise

FORGE_THRESHOLD_POINTS = 2


def get_forge_state_from_days(forge_days: int, cooling: bool = False) -> str:
    """Return the visible Forge state from the character's streak count."""
    if cooling and forge_days > 0:
        return "Cooling"
    if forge_days <= 0:
        return "Cold"
    if forge_days <= 2:
        return "Lit"
    if forge_days <= 6:
        return "Burning"
    if forge_days <= 13:
        return "Hot"
    return "Blazing"


def get_total_forge_points(daily_promises: list[DailyPromise]) -> int:
    return sum(promise.forge_points for promise in daily_promises)


def get_completed_forge_points(daily_promises: list[DailyPromise]) -> int:
    return sum(promise.forge_points for promise in daily_promises if promise.completion is not None)


def get_completed_count(daily_promises: list[DailyPromise]) -> int:
    return sum(1 for promise in daily_promises if promise.completion is not None)


def get_alignment_percent(daily_promises: list[DailyPromise]) -> int:
    total_points = get_total_forge_points(daily_promises)
    if total_points <= 0:
        return 0
    return round((get_completed_forge_points(daily_promises) / total_points) * 100)


def is_forge_active_today(daily_promises: list[DailyPromise]) -> bool:
    return get_completed_forge_points(daily_promises) >= FORGE_THRESHOLD_POINTS


def get_points_needed_today(daily_promises: list[DailyPromise]) -> int:
    return max(0, FORGE_THRESHOLD_POINTS - get_completed_forge_points(daily_promises))


def apply_forge_progress_after_completion(
    character: Character,
    before_completed_points: int,
    after_daily_promises: list[DailyPromise],
) -> bool:
    """Update character Forge state when today's Forge threshold is crossed.

    Returns True only on the moment the daily threshold is crossed.
    This prevents completing a second/third Promise on the same day from adding extra Forge days.
    """
    after_completed_points = get_completed_forge_points(after_daily_promises)
    threshold_crossed_now = before_completed_points < FORGE_THRESHOLD_POINTS <= after_completed_points

    character.today_alignment = get_alignment_percent(after_daily_promises)

    if threshold_crossed_now:
        character.forge_days = (character.forge_days or 0) + 1
        character.forge_cooling = False
        character.forge_state = get_forge_state_from_days(character.forge_days, cooling=False)
    else:
        character.forge_state = get_forge_state_from_days(character.forge_days or 0, cooling=bool(character.forge_cooling))

    return threshold_crossed_now


def sync_today_forge_state_if_needed(
    db: Session,
    character: Character,
    daily_promises: list[DailyPromise],
) -> bool:
    """Keep the visible Forge state honest for the current day.

    Earlier MVP steps kept the Character's Forge state as Lit/Burning even after days
    with no completed Promise. That made the UI look stale: a user could return after
    several missed days and still see Lit.

    Step 23 fixes the visible state without adding a database migration:
    - no Promises today, or not enough completed points today => Cooling
      when the character has any previous Forge days; otherwise Cold.
    - enough completed points today => active Forge state from the streak count.
    - Step 13 repair is preserved for users who completed enough points before the
      Forge-day increment existed.
    """
    completed_points = get_completed_forge_points(daily_promises)
    active_today = completed_points >= FORGE_THRESHOLD_POINTS

    character.today_alignment = get_alignment_percent(daily_promises)

    if active_today and (character.forge_days or 0) == 0:
        character.forge_days = 1
        character.forge_cooling = False
        character.forge_state = get_forge_state_from_days(1, cooling=False)
        db.commit()
        db.refresh(character)
        return True

    if active_today:
        character.forge_cooling = False
        character.forge_state = get_forge_state_from_days(character.forge_days or 0, cooling=False)
        db.commit()
        db.refresh(character)
        return False

    if (character.forge_days or 0) > 0:
        character.forge_cooling = True
        character.forge_state = get_forge_state_from_days(character.forge_days or 0, cooling=True)
    else:
        character.forge_cooling = False
        character.forge_state = get_forge_state_from_days(0, cooling=False)

    db.commit()
    db.refresh(character)
    return False


def build_forge_snapshot(character: Character, daily_promises: list[DailyPromise]) -> dict:
    completed_points = get_completed_forge_points(daily_promises)
    total_points = get_total_forge_points(daily_promises)
    active_today = completed_points >= FORGE_THRESHOLD_POINTS

    return {
        "forge_threshold_points": FORGE_THRESHOLD_POINTS,
        "forge_active_today": active_today,
        "forge_points_needed_today": max(0, FORGE_THRESHOLD_POINTS - completed_points),
        "forge_days": character.forge_days or 0,
        "forge_state": get_forge_state_from_days(character.forge_days or 0, cooling=bool(character.forge_cooling)),
        "forge_cooling": bool(character.forge_cooling),
        "today_alignment": get_alignment_percent(daily_promises),
        "selected_count": len(daily_promises),
        "completed_count": get_completed_count(daily_promises),
        "total_forge_points": total_points,
        "completed_forge_points": completed_points,
    }
