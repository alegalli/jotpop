from sqlalchemy.orm import Session

from app.models import Card
from app.seed.cards import INITIAL_CARDS


def seed_initial_cards(db: Session) -> int:
    """Insert the MVP card library in an idempotent way.

    Step 29 keeps the demo deck fresh by deactivating older generated
    ``expanded_feed`` cards that are no longer present in the seed set.
    This prevents the repetitive Step 27 cards from remaining mixed into
    the mobile Feed after the copy-quality pass.
    """
    inserted = 0
    seed_keys = {(card_data["title"], card_data["type"]) for card_data in INITIAL_CARDS}

    for card_data in INITIAL_CARDS:
        existing = (
            db.query(Card)
            .filter(
                Card.title == card_data["title"],
                Card.type == card_data["type"],
            )
            .first()
        )
        if existing is not None:
            # Keep seed data fresh while avoiding duplicate rows.
            for key, value in card_data.items():
                setattr(existing, key, value)
            existing.is_active = True
            continue

        db.add(Card(**card_data))
        inserted += 1

    for existing in db.query(Card).filter(Card.is_onboarding.is_(False)).all():
        tags = existing.tags or []
        if "expanded_feed" in tags and (existing.title, existing.type) not in seed_keys:
            existing.is_active = False

    db.commit()
    return inserted
