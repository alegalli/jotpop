from sqlalchemy.orm import Session

from app.models import Character, Jot, Signal


def clean_jot_content(content: str) -> str:
    return " ".join((content or "").strip().split())


def get_total_jots_for_character(db: Session, character: Character) -> int:
    return db.query(Jot).filter(Jot.character_id == character.id).count()


def get_latest_jots_for_character(
    db: Session,
    character: Character,
    limit: int = 5,
) -> list[Jot]:
    safe_limit = max(1, min(limit, 20))
    return (
        db.query(Jot)
        .filter(Jot.character_id == character.id)
        .order_by(Jot.created_at.desc(), Jot.id.desc())
        .limit(safe_limit)
        .all()
    )


def get_jot_path_message(total_jots: int) -> str:
    if total_jots <= 0:
        return "No Jots yet. The deck is still mostly generic."
    if total_jots == 1:
        return "One step off the popular path."
    if total_jots < 5:
        return "The path is starting to sound like you."
    if total_jots < 12:
        return "Your Jots are bending the map away from generic."
    return "The map is becoming yours."


def create_manual_jot_for_character(
    db: Session,
    character: Character,
    content: str,
    prompt: str | None = None,
) -> Jot:
    cleaned = clean_jot_content(content)
    jot = Jot(
        character_id=character.id,
        card_id=None,
        prompt=prompt or "Manual Jot",
        content=cleaned,
    )
    db.add(jot)
    db.flush()

    signal = Signal(
        character_id=character.id,
        card_interaction_id=None,
        source="jot_trail",
        action="manual_jot",
        accepted=True,
        tags=["jot", "reflection", "personal_signal"],
        weights={"Reflect": 0.25, "Create": 0.12, "Build": 0.08},
    )
    db.add(signal)

    character.total_signal_count = (character.total_signal_count or 0) + 1
    character.accepted_signal_count = (character.accepted_signal_count or 0) + 1

    db.commit()
    db.refresh(character)
    db.refresh(jot)
    return jot
