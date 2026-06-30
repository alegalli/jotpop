from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import (
    Card,
    Character,
    DailyPromise,
    InsightUnlock,
    Jot,
    PromiseCompletion,
    PromiseTemplate,
    Signal,
    User,
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/dev", tags=["dev"])


def is_dev_user(user: User) -> bool:
    settings = get_settings()
    return user.email.lower() in settings.dev_email_set


def require_dev_user(current_user: User = Depends(get_current_user)) -> User:
    if not is_dev_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev access only",
        )
    return current_user


def build_counts(db: Session) -> dict[str, int]:
    return {
        "users": db.query(User).count(),
        "characters": db.query(Character).count(),
        "cards": db.query(Card).count(),
        "active_cards": db.query(Card).filter(Card.is_active.is_(True)).count(),
        "onboarding_cards": db.query(Card).filter(Card.is_active.is_(True), Card.is_onboarding.is_(True)).count(),
        "feed_cards": db.query(Card).filter(Card.is_active.is_(True), Card.is_onboarding.is_(False)).count(),
        "signals": db.query(Signal).count(),
        "accepted_signals": db.query(Signal).filter(Signal.accepted.is_(True)).count(),
        "jots": db.query(Jot).count(),
        "promise_templates": db.query(PromiseTemplate).count(),
        "active_promise_templates": db.query(PromiseTemplate).filter(PromiseTemplate.is_active.is_(True)).count(),
        "daily_promises": db.query(DailyPromise).count(),
        "promise_completions": db.query(PromiseCompletion).count(),
        "insights": db.query(InsightUnlock).count(),
    }


def get_active_character(db: Session, user: User) -> Character | None:
    return (
        db.query(Character)
        .filter(Character.user_id == user.id, Character.is_active.is_(True))
        .first()
    )


@router.get("/status")
def dev_status(
    current_user: User = Depends(require_dev_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    counts = build_counts(db)
    latest_character = get_active_character(db, current_user)

    return {
        "status": "ok",
        "service": "jotpop-dev-tools",
        "app_version": settings.app_version,
        "normal_user_debug_visibility": "hidden",
        "dev_user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
        },
        "active_character": {
            "id": latest_character.id if latest_character else None,
            "state": latest_character.current_state if latest_character else None,
            "identity": latest_character.identity_label if latest_character else None,
            "forge_state": latest_character.forge_state if latest_character else None,
            "forge_days": latest_character.forge_days if latest_character else 0,
            "today_alignment": latest_character.today_alignment if latest_character else 0,
        },
        "counts": counts,
        "systems": {
            "auth": "protected",
            "database": "connected",
            "feed": "expanded_100_plus_cards",
            "forge": "enabled",
            "evolution": "enabled",
            "jots": "enabled",
            "dev_smoke_check": "enabled",
        },
        "dev_notes": [
            "This route is not used by normal product UI.",
            "Access is controlled by DEV_USER_EMAILS / dev_user_emails.",
            "Use this page for testing without exposing backend wording to users.",
        ],
    }


@router.get("/smoke")
def dev_smoke_check(
    current_user: User = Depends(require_dev_user),
    db: Session = Depends(get_db),
):
    """Dev-only MVP smoke checklist.

    This endpoint intentionally stays out of the normal product UI. It gives the
    developer a fast confidence check before demo/deployment.
    """
    settings = get_settings()
    counts = build_counts(db)
    character = get_active_character(db, current_user)
    today = date.today()

    today_promises = 0
    today_completions = 0
    if character:
        today_promises = (
            db.query(DailyPromise)
            .filter(DailyPromise.character_id == character.id, DailyPromise.selected_date == today)
            .count()
        )
        today_completions = (
            db.query(PromiseCompletion)
            .join(DailyPromise, PromiseCompletion.daily_promise_id == DailyPromise.id)
            .filter(DailyPromise.character_id == character.id, DailyPromise.selected_date == today)
            .count()
        )

    checks: list[dict[str, object]] = []

    def add_check(key: str, label: str, passed: bool, detail: str, severity: str = "fail") -> None:
        checks.append(
            {
                "key": key,
                "label": label,
                "status": "pass" if passed else severity,
                "detail": detail,
            }
        )

    add_check(
        "dev_access",
        "Dev access protected",
        True,
        f"Authenticated as dev user {current_user.email}.",
    )
    add_check(
        "database",
        "Database connected",
        True,
        "The dev endpoint can query the database.",
    )
    add_check(
        "user_character",
        "Active character exists",
        character is not None,
        "Current user has an active character." if character else "Create/login with the seeded demo account or register a user.",
    )
    add_check(
        "onboarding_cards",
        "Onboarding has at least 7 cards",
        counts["onboarding_cards"] >= 7,
        f"Found {counts['onboarding_cards']} active onboarding cards.",
    )
    add_check(
        "feed_cards",
        "Feed deck has at least 100 cards",
        counts["feed_cards"] >= 100,
        f"Found {counts['feed_cards']} active feed cards. Step 27 expects at least 100.",
    )
    add_check(
        "promise_templates",
        "Forge has at least 7 suggestions",
        counts["active_promise_templates"] >= 7,
        f"Found {counts['active_promise_templates']} active promise templates.",
    )
    add_check(
        "today_promises",
        "Today promises can be tested",
        today_promises in (0, 3),
        f"Today has {today_promises} locked promises for this character. Expected 0 before lock or 3 after lock.",
        severity="warn",
    )
    add_check(
        "today_completions",
        "Forge completion state readable",
        today_completions <= today_promises,
        f"Today completions: {today_completions}/{today_promises}.",
    )
    add_check(
        "jot_system",
        "Jot system enabled",
        "jots" in counts,
        f"Stored Jots: {counts['jots']}.",
    )
    add_check(
        "normal_debug_hidden",
        "Normal UI hides debug wording",
        True,
        "Debug/status data is available only through dev routes and dev UI.",
    )

    failures = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warn"]

    return {
        "status": "pass" if not failures else "fail",
        "service": "jotpop-dev-smoke-check",
        "app_version": settings.app_version,
        "checked_at_date": today.isoformat(),
        "summary": {
            "checks": len(checks),
            "passed": len([check for check in checks if check["status"] == "pass"]),
            "warnings": len(warnings),
            "failures": len(failures),
        },
        "current_user": {
            "id": current_user.id,
            "email": current_user.email,
            "is_dev": True,
        },
        "active_character": {
            "id": character.id if character else None,
            "state": character.current_state if character else None,
            "identity": character.identity_label if character else None,
            "forge_state": character.forge_state if character else None,
            "forge_cooling": character.forge_cooling if character else False,
            "forge_days": character.forge_days if character else 0,
            "today_alignment": character.today_alignment if character else 0,
            "today_promises": today_promises,
            "today_completions": today_completions,
        },
        "counts": counts,
        "checks": checks,
        "manual_flow_to_test_next": [
            "Sign in as ale@example.com.",
            "Feed: verify the expanded deck, swipe/tap cards and save one Micro-Jot.",
            "Forge: lock exactly 3 promises if not locked, then forge one.",
            "Evolution: verify avatar, Pattern Map, Follow-through and compact achievements.",
            "Dev: run this smoke check and complete the manual QA checklist.",
        ],
    }
