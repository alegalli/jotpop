from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import Character, User
from app.schemas.auth import RegisterRequest


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_with_character(db: Session, payload: RegisterRequest) -> User:
    display_name = payload.display_name or payload.username or payload.email.split("@")[0]

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    character = Character(
        user_id=user.id,
        display_name=display_name,
        current_state="Exploring",
        identity_label="Undiscovered",
        accepted_signal_count=0,
        total_signal_count=0,
        forge_days=0,
        forge_state="Cold",
        forge_cooling=False,
        today_alignment=0,
        is_active=True,
    )
    db.add(character)
    db.commit()
    db.refresh(user)
    return user


def get_active_character(user: User) -> Character | None:
    for character in user.characters:
        if character.is_active:
            return character
    return user.characters[0] if user.characters else None
