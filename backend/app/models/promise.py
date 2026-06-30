from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class PromiseTemplate(Base):
    __tablename__ = "promise_templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False)
    forge_points = Column(Integer, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    suggestion_weight = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    daily_promises = relationship("DailyPromise", back_populates="template")


class DailyPromise(Base):
    __tablename__ = "daily_promises"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("promise_templates.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    difficulty = Column(String(20), nullable=False)
    forge_points = Column(Integer, nullable=False)
    selected_date = Column(Date, default=date.today, nullable=False, index=True)
    is_system_proposed = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    character = relationship("Character", back_populates="daily_promises")
    template = relationship("PromiseTemplate", back_populates="daily_promises")
    completion = relationship("PromiseCompletion", back_populates="daily_promise", uselist=False, cascade="all, delete-orphan")


class PromiseCompletion(Base):
    __tablename__ = "promise_completions"

    id = Column(Integer, primary_key=True, index=True)
    daily_promise_id = Column(Integer, ForeignKey("daily_promises.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    proof_text = Column(Text, nullable=True)

    daily_promise = relationship("DailyPromise", back_populates="completion")
