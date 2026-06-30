from app.db.base import Base
from app.db.session import SessionLocal, engine

# Import models so SQLAlchemy knows them before create_all().
from app.models import (  # noqa: F401
    Achievement,
    Card,
    CardInteraction,
    Character,
    CharacterAchievement,
    DailyPromise,
    InsightUnlock,
    Jot,
    PromiseCompletion,
    PromiseTemplate,
    Signal,
    User,
)
from app.services.seed_service import seed_initial_cards
from app.services.promise_service import seed_initial_promise_templates


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_initial_cards(db)
        seed_initial_promise_templates(db)
    finally:
        db.close()
