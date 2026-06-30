from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Character, InsightUnlock, Signal

INSIGHT_THRESHOLD = 50


def _next_threshold_for_character(db: Session, character: Character) -> int:
    highest = (
        db.query(InsightUnlock.threshold)
        .filter(InsightUnlock.character_id == character.id)
        .order_by(InsightUnlock.threshold.desc())
        .first()
    )
    if highest is None:
        return INSIGHT_THRESHOLD
    return int(highest[0]) + INSIGHT_THRESHOLD


def _summarize_accepted_signals(db: Session, character: Character) -> tuple[list[str], str]:
    signals = (
        db.query(Signal)
        .filter(Signal.character_id == character.id, Signal.accepted.is_(True))
        .order_by(Signal.created_at.desc(), Signal.id.desc())
        .limit(80)
        .all()
    )

    tag_counter: Counter[str] = Counter()
    weight_counter: Counter[str] = Counter()

    for signal in signals:
        for tag in signal.tags or []:
            if isinstance(tag, str) and tag.strip():
                tag_counter[tag.strip()] += 1
        for key, value in (signal.weights or {}).items():
            try:
                weight_counter[str(key)] += int(value)
            except (TypeError, ValueError):
                continue

    top_tags = [tag for tag, _ in tag_counter.most_common(5)]
    top_weights = [weight for weight, _ in weight_counter.most_common(3)]

    if top_tags and top_weights:
        content = (
            f"Your first pattern is forming around {', '.join(top_tags[:3])}. "
            f"The strongest repeated signals point toward {', '.join(top_weights[:2])}. "
            "This is not your final identity; it is the first evidence trail of who you are becoming."
        )
    elif top_tags:
        content = (
            f"Your first pattern is forming around {', '.join(top_tags[:3])}. "
            "The app has enough accepted signals to show an early direction, but not enough to name a final identity."
        )
    else:
        content = (
            "Your first 50 accepted signals are now stored. The pattern is still faint, but one thing is clear: "
            "you are no longer only exploring. You are leaving a trail the system can read."
        )

    tags = top_tags or ["early-pattern", "exploring"]
    return tags, content


def check_and_create_insight_unlocks(db: Session, character: Character) -> list[InsightUnlock]:
    created: list[InsightUnlock] = []

    while (character.accepted_signal_count or 0) >= _next_threshold_for_character(db, character):
        threshold = _next_threshold_for_character(db, character)
        tags, content = _summarize_accepted_signals(db, character)
        title = "First Pattern Emerges" if threshold == INSIGHT_THRESHOLD else f"Pattern Deepened at {threshold} Signals"

        insight = InsightUnlock(
            character_id=character.id,
            threshold=threshold,
            title=title,
            content=content,
            tags=tags,
        )
        db.add(insight)
        db.flush()
        created.append(insight)

    return created


def get_insight_status(db: Session, character: Character) -> dict:
    check_and_create_insight_unlocks(db, character)
    db.commit()

    insights = (
        db.query(InsightUnlock)
        .filter(InsightUnlock.character_id == character.id)
        .order_by(InsightUnlock.threshold.desc(), InsightUnlock.id.desc())
        .all()
    )
    unlocked_count = len(insights)
    next_threshold = _next_threshold_for_character(db, character)
    accepted_count = character.accepted_signal_count or 0
    signals_until_next = max(0, next_threshold - accepted_count)
    unresponded = [insight for insight in insights if insight.accepted is None]

    return {
        "status": "ok",
        "accepted_signal_count": accepted_count,
        "total_signal_count": character.total_signal_count or 0,
        "insight_threshold": INSIGHT_THRESHOLD,
        "unlocked_count": unlocked_count,
        "next_threshold": next_threshold,
        "signals_until_next_unlock": signals_until_next,
        "unlock_available": bool(unresponded),
        "latest_unlocked": insights[0] if insights else None,
        "unresponded_insights": unresponded,
    }


def list_insights_for_character(db: Session, character: Character) -> list[InsightUnlock]:
    check_and_create_insight_unlocks(db, character)
    db.commit()
    return (
        db.query(InsightUnlock)
        .filter(InsightUnlock.character_id == character.id)
        .order_by(InsightUnlock.threshold.desc(), InsightUnlock.id.desc())
        .all()
    )


def respond_to_insight(db: Session, character: Character, insight_id: int, accepted: bool) -> InsightUnlock | None:
    insight = (
        db.query(InsightUnlock)
        .filter(InsightUnlock.id == insight_id, InsightUnlock.character_id == character.id)
        .first()
    )
    if insight is None:
        return None

    insight.accepted = accepted
    insight.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(insight)
    return insight
