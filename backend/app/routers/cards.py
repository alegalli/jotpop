from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Card
from app.schemas.card import CardResponse, CardStatsResponse

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/onboarding", response_model=list[CardResponse])
def get_onboarding_cards(db: Session = Depends(get_db)) -> list[Card]:
    """Return the exact 7 pre-account onboarding cards."""
    return (
        db.query(Card)
        .filter(Card.is_active.is_(True), Card.is_onboarding.is_(True))
        .order_by(Card.position.asc(), Card.id.asc())
        .limit(7)
        .all()
    )


@router.get("/feed", response_model=list[CardResponse])
def get_feed_cards(
    limit: int = Query(default=120, ge=1, le=150),
    db: Session = Depends(get_db),
) -> list[Card]:
    """Return the expanded active feed deck.

Step 27 raises the default limit so the frontend can load the richer demo deck.
"""
    return (
        db.query(Card)
        .filter(Card.is_active.is_(True), Card.is_onboarding.is_(False))
        .order_by(Card.position.asc(), Card.id.asc())
        .limit(limit)
        .all()
    )


@router.get("/stats", response_model=CardStatsResponse)
def get_card_stats(db: Session = Depends(get_db)) -> CardStatsResponse:
    total_cards = db.query(Card).filter(Card.is_active.is_(True)).count()
    onboarding_cards = (
        db.query(Card)
        .filter(Card.is_active.is_(True), Card.is_onboarding.is_(True))
        .count()
    )
    feed_cards = (
        db.query(Card)
        .filter(Card.is_active.is_(True), Card.is_onboarding.is_(False))
        .count()
    )

    return CardStatsResponse(
        status="ok" if onboarding_cards >= 7 else "missing_onboarding_cards",
        total_cards=total_cards,
        onboarding_cards=onboarding_cards,
        feed_cards=feed_cards,
        expected_onboarding_cards=7,
        onboarding_ready=onboarding_cards >= 7,
    )
