from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from app.models import Card, Character, DailyPromise, PromiseCompletion, PromiseTemplate
from app.seed.promises import INITIAL_PROMISE_TEMPLATES
from app.services.forge_service import (
    FORGE_THRESHOLD_POINTS,
    apply_forge_progress_after_completion,
    build_forge_snapshot,
    get_alignment_percent,
    get_completed_count,
    get_completed_forge_points,
    get_total_forge_points,
    sync_today_forge_state_if_needed,
)

REQUIRED_DAILY_PROMISE_COUNT = 3



def _difficulty_from_card(card: Card) -> str:
    tags = [str(tag).lower() for tag in (card.tags or [])]
    title = (card.title or "").lower()
    text = " ".join(tags + [title])
    if any(word in text for word in ["hard", "deep", "brave", "build", "launch"]):
        return "hard"
    if any(word in text for word in ["easy", "small", "tiny", "quick"]):
        return "easy"
    return "medium"


def _forge_points_for_difficulty(difficulty: str) -> int:
    if difficulty == "hard":
        return 3
    if difficulty == "easy":
        return 1
    return 2


def add_feed_challenge_to_today_promises(
    db: Session,
    character: Character,
    card: Card,
    selected_date: date | None = None,
) -> tuple[DailyPromise | None, bool]:
    """Turn an accepted Feed challenge into a Daily Promise.

    If today already has fewer than 3 Promises, the challenge becomes one of
    the first 3. If today already has 3 or more, the challenge is appended as
    an extra optional Promise for the day.
    """
    day = selected_date or date.today()
    title = (card.title or "Accepted Feed challenge").strip()[:255]
    existing = get_today_daily_promises(db, character.id, day)

    for promise in existing:
        if promise.title.strip().lower() == title.lower():
            return promise, False

    difficulty = _difficulty_from_card(card)
    daily_promise = DailyPromise(
        character_id=character.id,
        template_id=None,
        title=title,
        difficulty=difficulty,
        forge_points=_forge_points_for_difficulty(difficulty),
        selected_date=day,
        is_system_proposed=False,
        is_locked=len(existing) + 1 >= REQUIRED_DAILY_PROMISE_COUNT,
    )
    db.add(daily_promise)
    return daily_promise, True


def seed_initial_promise_templates(db: Session) -> int:
    """Insert MVP promise templates in an idempotent way."""
    inserted = 0

    for template_data in INITIAL_PROMISE_TEMPLATES:
        existing = (
            db.query(PromiseTemplate)
            .filter(PromiseTemplate.title == template_data["title"])
            .first()
        )
        if existing is not None:
            for key, value in template_data.items():
                setattr(existing, key, value)
            continue

        db.add(PromiseTemplate(**template_data))
        inserted += 1

    db.commit()
    return inserted


def get_active_promise_templates(db: Session) -> list[PromiseTemplate]:
    return (
        db.query(PromiseTemplate)
        .filter(PromiseTemplate.is_active.is_(True))
        .order_by(PromiseTemplate.suggestion_weight.desc(), PromiseTemplate.id.asc())
        .all()
    )


def get_today_promise_suggestions(db: Session, limit: int = 7) -> list[PromiseTemplate]:
    return get_active_promise_templates(db)[:limit]


def get_today_daily_promises(
    db: Session,
    character_id: int,
    selected_date: date | None = None,
) -> list[DailyPromise]:
    day = selected_date or date.today()
    return (
        db.query(DailyPromise)
        .filter(
            DailyPromise.character_id == character_id,
            DailyPromise.selected_date == day,
        )
        .order_by(DailyPromise.created_at.asc(), DailyPromise.id.asc())
        .all()
    )


def select_today_promises(
    db: Session,
    character: Character,
    template_ids: list[int],
    selected_date: date | None = None,
) -> list[DailyPromise]:
    day = selected_date or date.today()
    template_ids = template_ids or []

    existing = get_today_daily_promises(db, character.id, day)
    if len(existing) >= REQUIRED_DAILY_PROMISE_COUNT:
        raise ValueError("Today's Promises are already locked.")

    remaining_slots = REQUIRED_DAILY_PROMISE_COUNT - len(existing)
    if len(template_ids) != remaining_slots:
        raise ValueError(f"Choose {remaining_slots} more Promises.")

    if len(set(template_ids)) != len(template_ids):
        raise ValueError("Choose different Promises.")

    existing_template_ids = {promise.template_id for promise in existing if promise.template_id is not None}
    duplicated_existing = [template_id for template_id in template_ids if template_id in existing_template_ids]
    if duplicated_existing:
        raise ValueError("This Promise is already selected for today.")

    templates = (
        db.query(PromiseTemplate)
        .filter(
            PromiseTemplate.id.in_(template_ids),
            PromiseTemplate.is_active.is_(True),
        )
        .all()
        if template_ids
        else []
    )

    templates_by_id = {template.id: template for template in templates}
    missing_ids = [template_id for template_id in template_ids if template_id not in templates_by_id]
    if missing_ids:
        raise ValueError(f"Promise template not found or inactive: {missing_ids}")

    for promise in existing:
        promise.is_locked = True

    daily_promises: list[DailyPromise] = list(existing)
    for template_id in template_ids:
        template = templates_by_id[template_id]
        daily_promise = DailyPromise(
            character_id=character.id,
            template_id=template.id,
            title=template.title,
            difficulty=template.difficulty,
            forge_points=template.forge_points,
            selected_date=day,
            is_system_proposed=True,
            is_locked=True,
        )
        db.add(daily_promise)
        daily_promises.append(daily_promise)

    character.today_alignment = 0
    db.commit()
    for daily_promise in daily_promises:
        db.refresh(daily_promise)

    return get_today_daily_promises(db, character.id, day)

def complete_daily_promise(
    db: Session,
    character: Character,
    daily_promise_id: int,
    proof_text: str | None = None,
    selected_date: date | None = None,
) -> tuple[DailyPromise, bool]:
    day = selected_date or date.today()

    daily_promise = (
        db.query(DailyPromise)
        .filter(
            DailyPromise.id == daily_promise_id,
            DailyPromise.character_id == character.id,
        )
        .first()
    )

    if daily_promise is None:
        raise ValueError("Daily Promise not found for this character.")

    if daily_promise.selected_date != day:
        raise ValueError("Only today's Promises can be forged in the MVP.")

    if daily_promise.completion is not None:
        raise ValueError("This Promise has already been forged.")

    before_promises = get_today_daily_promises(db, character.id, day)
    before_completed_points = get_completed_forge_points(before_promises)

    completion = PromiseCompletion(
        daily_promise_id=daily_promise.id,
        proof_text=proof_text.strip() if proof_text else None,
    )
    db.add(completion)
    db.flush()

    todays_promises = get_today_daily_promises(db, character.id, day)
    threshold_crossed_now = apply_forge_progress_after_completion(
        character=character,
        before_completed_points=before_completed_points,
        after_daily_promises=todays_promises,
    )

    db.commit()
    db.refresh(daily_promise)
    db.refresh(character)
    return daily_promise, threshold_crossed_now


def daily_promise_to_response_data(daily_promise: DailyPromise) -> dict:
    completion = daily_promise.completion
    return {
        "id": daily_promise.id,
        "character_id": daily_promise.character_id,
        "template_id": daily_promise.template_id,
        "title": daily_promise.title,
        "difficulty": daily_promise.difficulty,
        "forge_points": daily_promise.forge_points,
        "selected_date": daily_promise.selected_date,
        "is_system_proposed": daily_promise.is_system_proposed,
        "is_locked": daily_promise.is_locked,
        "created_at": daily_promise.created_at,
        "completed": completion is not None,
        "completed_at": completion.completed_at if completion is not None else None,
    }


def get_promise_template_stats(db: Session) -> dict:
    templates = db.query(PromiseTemplate).all()
    active_templates = [template for template in templates if template.is_active]
    difficulty_counts = Counter(template.difficulty for template in active_templates)

    return {
        "total_templates": len(templates),
        "active_templates": len(active_templates),
        "difficulty_counts": dict(sorted(difficulty_counts.items())),
    }


def get_today_forge_snapshot(db: Session, character: Character) -> dict:
    daily_promises = get_today_daily_promises(db, character.id)
    sync_today_forge_state_if_needed(db, character, daily_promises)
    return build_forge_snapshot(character, daily_promises)
