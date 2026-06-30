from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(Text, nullable=True)

    options = Column(JSON, default=list, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    signal_weights = Column(JSON, default=dict, nullable=False)

    visual_theme = Column(String(50), default="signal", nullable=False)
    icon = Column(String(20), default="✦", nullable=False)
    position = Column(Integer, default=0, nullable=False)

    is_onboarding = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interactions = relationship("CardInteraction", back_populates="card", cascade="all, delete-orphan")


class CardInteraction(Base):
    __tablename__ = "card_interactions"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)

    action = Column(String(50), nullable=False)
    selected_option = Column(String(255), nullable=True)
    accepted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    character = relationship("Character", back_populates="card_interactions")
    card = relationship("Card", back_populates="interactions")
    signal = relationship("Signal", back_populates="card_interaction", uselist=False)
