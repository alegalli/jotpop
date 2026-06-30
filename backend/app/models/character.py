from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    display_name = Column(String(120), nullable=False)
    current_state = Column(String(80), default="Exploring", nullable=False)
    identity_label = Column(String(120), default="Undiscovered", nullable=False)

    accepted_signal_count = Column(Integer, default=0, nullable=False)
    total_signal_count = Column(Integer, default=0, nullable=False)

    forge_days = Column(Integer, default=0, nullable=False)
    forge_state = Column(String(50), default="Cold", nullable=False)
    forge_cooling = Column(Boolean, default=False, nullable=False)
    today_alignment = Column(Integer, default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="characters")
    card_interactions = relationship("CardInteraction", back_populates="character", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="character", cascade="all, delete-orphan")
    jots = relationship("Jot", back_populates="character", cascade="all, delete-orphan")
    daily_promises = relationship("DailyPromise", back_populates="character", cascade="all, delete-orphan")
    achievements = relationship("CharacterAchievement", back_populates="character", cascade="all, delete-orphan")
    insight_unlocks = relationship("InsightUnlock", back_populates="character", cascade="all, delete-orphan")
