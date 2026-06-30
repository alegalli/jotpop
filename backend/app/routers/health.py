from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine, get_db
from app.models import Card, Character, DailyPromise, InsightUnlock, PromiseCompletion, PromiseTemplate, Signal

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "jotpop-api",
        "version": settings.app_version,
    }


@router.get("/config")
def config_health():
    settings = get_settings()
    return {
        "status": "ok",
        "backend_port": settings.backend_port,
        "frontend_port": settings.frontend_port,
        "jwt_algorithm": settings.jwt_algorithm,
        "database_url_loaded": bool(settings.database_url),
    }


@router.get("/db")
def database_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar_one()
    return {
        "status": "ok",
        "database": "connected",
        "result": result,
    }


@router.get("/tables")
def tables_health():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = set(Base.metadata.tables.keys())
    missing_tables = sorted(expected_tables - existing_tables)

    return {
        "status": "ok" if not missing_tables else "missing_tables",
        "expected_count": len(expected_tables),
        "existing_count": len(existing_tables.intersection(expected_tables)),
        "expected_tables": sorted(expected_tables),
        "existing_tables": sorted(existing_tables),
        "missing_tables": missing_tables,
    }


@router.get("/cards")
def cards_health(db: Session = Depends(get_db)):
    onboarding_cards = (
        db.query(Card)
        .filter(Card.is_active.is_(True), Card.is_onboarding.is_(True))
        .count()
    )
    total_cards = db.query(Card).filter(Card.is_active.is_(True)).count()

    return {
        "status": "ok" if onboarding_cards >= 7 else "missing_onboarding_cards",
        "total_cards": total_cards,
        "onboarding_cards": onboarding_cards,
        "expected_onboarding_cards": 7,
        "onboarding_ready": onboarding_cards >= 7,
    }


@router.get("/promises")
def promises_health(db: Session = Depends(get_db)):
    active_templates = (
        db.query(PromiseTemplate)
        .filter(PromiseTemplate.is_active.is_(True))
        .count()
    )
    total_templates = db.query(PromiseTemplate).count()

    return {
        "status": "ok" if active_templates >= 7 else "missing_templates",
        "total_templates": total_templates,
        "active_templates": active_templates,
        "expected_minimum_templates": 7,
        "templates_ready": active_templates >= 7,
    }


@router.get("/signals")
def signals_health(db: Session = Depends(get_db)):
    total_signals = db.query(Signal).count()
    accepted_signals = db.query(Signal).filter(Signal.accepted.is_(True)).count()

    return {
        "status": "ok",
        "total_signals": total_signals,
        "accepted_signals": accepted_signals,
        "signal_system_ready": True,
    }

@router.get("/forge")
def forge_health(db: Session = Depends(get_db)):
    daily_promises = db.query(DailyPromise).count()
    completions = db.query(PromiseCompletion).count()
    characters = db.query(Character).count()

    return {
        "status": "ok",
        "daily_promises": daily_promises,
        "promise_completions": completions,
        "characters": characters,
        "forge_threshold_points": 2,
        "forge_states": ["Cold", "Lit", "Burning", "Hot", "Blazing", "Cooling"],
        "swipe_to_forge_ready": True,
        "forge_logic_ready": True,
    }



@router.get("/alignment")
def alignment_health(db: Session = Depends(get_db)):
    daily_promises = db.query(DailyPromise).count()
    completions = db.query(PromiseCompletion).count()

    return {
        "status": "ok",
        "daily_promises": daily_promises,
        "promise_completions": completions,
        "alignment_question": "Did you do what mattered?",
        "alignment_logic_ready": True,
        "labels": ["Unchosen", "Unstarted", "Misaligned", "Partly Aligned", "Aligned", "Fully Aligned"],
    }


@router.get("/insights")
def insights_health(db: Session = Depends(get_db)):
    insights = db.query(InsightUnlock).count()
    characters = db.query(Character).count()

    return {
        "status": "ok",
        "insight_threshold": 50,
        "insight_unlocks": insights,
        "characters": characters,
        "insight_system_ready": True,
        "rule": "Every 50 accepted signals unlocks one Insight Card.",
    }


@router.get("/evolution")
def evolution_health(db: Session = Depends(get_db)):
    characters = db.query(Character).count()
    insights = db.query(InsightUnlock).count()

    return {
        "status": "ok",
        "characters": characters,
        "insight_unlocks": insights,
        "evolution_page_ready": True,
        "subtitle": "Who I am becoming.",
        "sections": [
            "Character Snapshot",
            "Unlocked Card Types",
            "Achievements",
            "Insights",
            "Next Unlock",
        ],
    }
