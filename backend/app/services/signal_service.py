from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Card, CardInteraction, Character, Jot, Signal
from app.schemas.signal import CardSignalCreateRequest, SignalImportRequest
from app.services.insight_service import check_and_create_insight_unlocks
from app.services.promise_service import add_feed_challenge_to_today_promises


def _get_weights_for_choice(card: Card, choice: str | None) -> dict:
    weights = card.signal_weights or {}
    if isinstance(weights, dict) and choice:
        choice_weights = weights.get(choice)
        if isinstance(choice_weights, dict):
            return choice_weights
    return {}


def import_onboarding_signals_for_character(
    db: Session,
    character: Character,
    payload: SignalImportRequest,
) -> tuple[int, int, int]:
    imported = 0
    skipped = 0
    accepted_imported = 0

    for temporary_signal in payload.signals:
        card = (
            db.query(Card)
            .filter(Card.id == temporary_signal.card_id, Card.is_active.is_(True))
            .first()
        )

        if card is None:
            skipped += 1
            continue

        action = temporary_signal.direction or "tap"
        selected_option = temporary_signal.choice
        accepted = bool(temporary_signal.accepted)

        tags = temporary_signal.tags or card.tags or []
        weights = temporary_signal.signal_weights or _get_weights_for_choice(card, selected_option)

        interaction = CardInteraction(
            character_id=character.id,
            card_id=card.id,
            action=action,
            selected_option=selected_option,
            accepted=accepted,
        )
        db.add(interaction)
        db.flush()

        signal = Signal(
            character_id=character.id,
            card_interaction_id=interaction.id,
            source="onboarding_import",
            action=action,
            accepted=accepted,
            tags=tags,
            weights=weights,
        )
        db.add(signal)

        imported += 1
        if accepted:
            accepted_imported += 1

    character.total_signal_count = (character.total_signal_count or 0) + imported
    character.accepted_signal_count = (character.accepted_signal_count or 0) + accepted_imported
    check_and_create_insight_unlocks(db, character)

    db.commit()
    db.refresh(character)

    return imported, skipped, accepted_imported


def create_card_signal_for_character(
    db: Session,
    character: Character,
    payload: CardSignalCreateRequest,
) -> Signal:
    card = (
        db.query(Card)
        .filter(
            Card.id == payload.card_id,
            Card.is_active.is_(True),
            Card.is_onboarding.is_(False),
        )
        .first()
    )

    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active feed card not found",
        )

    action = payload.direction or "tap"
    selected_option = payload.choice or "submitted"
    accepted = bool(payload.accepted)

    if card.type == "micro_jot":
        # Empty Micro-Jots can be skipped with an upward swipe. Only an actual
        # Micro-Jot submission requires text.
        if action == "skip" or accepted is False:
            selected_option = "skipped"
            accepted = False
        else:
            jot_text = (payload.jot_text or "").strip()
            if not jot_text:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Micro-Jot text is required",
                )
            if len(jot_text) > 140:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Micro-Jot must be 140 characters or fewer",
                )
            selected_option = "submitted"
            accepted = True

            jot = Jot(
                character_id=character.id,
                card_id=card.id,
                prompt=card.title,
                content=jot_text,
            )
            db.add(jot)

    if card.type == "challenge" and accepted:
        # A challenge accepted from the Feed becomes part of today's Forge.
        # If the day is not fully shaped yet, it counts as one of the first 3.
        # If the day is already shaped, it becomes an extra optional Promise.
        add_feed_challenge_to_today_promises(db=db, character=character, card=card)

    interaction = CardInteraction(
        character_id=character.id,
        card_id=card.id,
        action=action,
        selected_option=selected_option,
        accepted=accepted,
    )
    db.add(interaction)
    db.flush()

    signal = Signal(
        character_id=character.id,
        card_interaction_id=interaction.id,
        source="discovery_feed",
        action=action,
        accepted=accepted,
        tags=card.tags or [],
        weights=_get_weights_for_choice(card, selected_option),
    )
    db.add(signal)

    character.total_signal_count = (character.total_signal_count or 0) + 1
    if accepted:
        character.accepted_signal_count = (character.accepted_signal_count or 0) + 1
    check_and_create_insight_unlocks(db, character)

    db.commit()
    db.refresh(character)
    db.refresh(signal)

    return signal


def get_latest_signals_for_character(
    db: Session,
    character: Character,
    limit: int = 20,
) -> list[Signal]:
    return (
        db.query(Signal)
        .filter(Signal.character_id == character.id)
        .order_by(Signal.created_at.desc(), Signal.id.desc())
        .limit(limit)
        .all()
    )
