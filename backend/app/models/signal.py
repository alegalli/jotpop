from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    card_interaction_id = Column(Integer, ForeignKey("card_interactions.id", ondelete="SET NULL"), nullable=True, index=True)

    source = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    accepted = Column(Boolean, default=False, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    weights = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    character = relationship("Character", back_populates="signals")
    card_interaction = relationship("CardInteraction", back_populates="signal")
