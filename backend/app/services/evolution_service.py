from datetime import date

from sqlalchemy.orm import Session

from app.models import Character, InsightUnlock
from app.services.forge_service import build_forge_snapshot, sync_today_forge_state_if_needed
from app.services.alignment_service import build_alignment_snapshot, sync_today_alignment
from app.services.promise_service import get_today_daily_promises

INSIGHT_THRESHOLD = 50


def _build_achievements(character: Character, selected_count: int, completed_count: int, unlocked_insights_count: int) -> list[dict]:
    total_signals = character.total_signal_count or 0
    accepted_signals = character.accepted_signal_count or 0
    forge_days = character.forge_days or 0

    achievements = [
        {
            "code": "first_account_created",
            "title": "First Account Created",
            "description": "You gave your evolving Character a place to live.",
            "icon": "🌱",
            "unlocked": True,
        },
        {
            "code": "first_signal",
            "title": "First Signal",
            "description": "The system received its first clue about who you are becoming.",
            "icon": "✦",
            "unlocked": total_signals >= 1,
        },
        {
            "code": "seven_signals",
            "title": "7 Signals Captured",
            "description": "Your first onboarding pattern is no longer empty.",
            "icon": "🜁",
            "unlocked": total_signals >= 7,
        },
        {
            "code": "first_promise_selected",
            "title": "First Promises Locked",
            "description": "You chose exactly 3 Promises for the day.",
            "icon": "🤝",
            "unlocked": selected_count >= 3,
        },
        {
            "code": "first_promise_forged",
            "title": "First Promise Forged",
            "description": "A Promise moved from intention into action.",
            "icon": "🔥",
            "unlocked": completed_count >= 1,
        },
        {
            "code": "forge_lit",
            "title": "Forge Lit",
            "description": "You crossed the daily Forge threshold.",
            "icon": "⚒️",
            "unlocked": forge_days >= 1,
        },
        {
            "code": "fifty_accepted_signals",
            "title": "50 Accepted Signals",
            "description": "Enough accepted signals exist for the first real Insight Card.",
            "icon": "✨",
            "unlocked": accepted_signals >= 50,
        },
        {
            "code": "first_insight_unlocked",
            "title": "First Insight Unlocked",
            "description": "The app reflected a pattern back to you.",
            "icon": "🔮",
            "unlocked": unlocked_insights_count >= 1,
        },
    ]
    return achievements


def _unlocked_card_types(unlocked_insights_count: int) -> list[str]:
    card_types = [
        "Tap Card",
        "This-or-That Card",
        "Swipe Card",
        "Challenge Card",
        "Micro-Jot Card",
    ]
    if unlocked_insights_count >= 1:
        card_types.append("Insight Card")
    return card_types


def build_evolution_summary(db: Session, character: Character) -> dict:
    today = date.today()
    daily_promises = get_today_daily_promises(db, character.id, today)
    sync_today_forge_state_if_needed(db, character, daily_promises)
    sync_today_alignment(db, character, daily_promises)

    forge_snapshot = build_forge_snapshot(character, daily_promises)
    alignment_snapshot = build_alignment_snapshot(character, daily_promises, today)

    insights = (
        db.query(InsightUnlock)
        .filter(InsightUnlock.character_id == character.id)
        .order_by(InsightUnlock.unlocked_at.desc(), InsightUnlock.id.desc())
        .all()
    )

    accepted_signals = character.accepted_signal_count or 0
    unlocked_insights_count = len(insights)
    next_threshold = ((accepted_signals // INSIGHT_THRESHOLD) + 1) * INSIGHT_THRESHOLD
    signals_until_next = max(0, next_threshold - accepted_signals)

    selected_count = len(daily_promises)
    completed_count = sum(1 for promise in daily_promises if promise.completion is not None)

    achievements = _build_achievements(character, selected_count, completed_count, unlocked_insights_count)
    unlocked_count = sum(1 for achievement in achievements if achievement["unlocked"])

    return {
        "status": "ok",
        "title": "Evolution",
        "subtitle": "Who I am becoming.",
        "character": {
            "id": character.id,
            "display_name": character.display_name,
            "current_state": character.current_state,
            "identity_label": character.identity_label,
            "accepted_signal_count": character.accepted_signal_count,
            "total_signal_count": character.total_signal_count,
            "forge_state": forge_snapshot["forge_state"],
            "forge_days": forge_snapshot["forge_days"],
            "forge_cooling": forge_snapshot["forge_cooling"],
            "today_alignment": alignment_snapshot["alignment_percent"],
            "created_at": character.created_at,
        },
        "metrics": [
            {"label": "Current State", "value": character.current_state, "helper": "The starting identity state."},
            {"label": "Identity", "value": character.identity_label, "helper": "Undiscovered until stronger patterns emerge."},
            {"label": "Accepted Signals", "value": accepted_signals, "helper": "Signals that count toward Insight unlocks."},
            {"label": "Total Signals", "value": character.total_signal_count or 0, "helper": "All saved signals, including rejections."},
            {"label": "Forge", "value": forge_snapshot["forge_state"], "helper": f'{forge_snapshot["forge_days"]} Forge day(s).'},
            {"label": "Alignment", "value": f'{alignment_snapshot["alignment_percent"]}%', "helper": alignment_snapshot["alignment_label"]},
            {"label": "Achievements", "value": unlocked_count, "helper": f'{unlocked_count}/{len(achievements)} unlocked.'},
            {"label": "Insights", "value": unlocked_insights_count, "helper": "Insight Cards unlocked so far."},
        ],
        "unlocked_card_types": _unlocked_card_types(unlocked_insights_count),
        "achievements": achievements,
        "insights": [
            {
                "id": insight.id,
                "threshold": insight.threshold,
                "title": insight.title,
                "content": insight.content,
                "tags": insight.tags or [],
                "accepted": insight.accepted,
                "unlocked_at": insight.unlocked_at,
                "responded_at": insight.responded_at,
            }
            for insight in insights
        ],
        "next_unlock": {
            "insight_threshold": INSIGHT_THRESHOLD,
            "next_threshold": next_threshold,
            "signals_until_next_unlock": signals_until_next,
            "progress_percent": min(100, round((accepted_signals / next_threshold) * 100)) if next_threshold else 0,
            "rule": "Every 50 accepted signals unlocks one Insight Card.",
        },
    }
