from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(80), unique=True, index=True, nullable=False)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(20), default="🏆", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    character_achievements = relationship("CharacterAchievement", back_populates="achievement")


class CharacterAchievement(Base):
    __tablename__ = "character_achievements"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    character = relationship("Character", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="character_achievements")
