from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class DailyTask(Base):
    """Practical task for one user on one local calendar date.

    This is intentionally separate from Forge promises. Daily tasks are the
    operational execution layer; Forge remains the identity/promise layer.
    """

    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    task_date = Column(Date, nullable=False, index=True)

    # planned / completed / moved / dropped / deleted_shadow
    status = Column(String(40), default="planned", nullable=False, index=True)

    # manual / plan / minimum_day / feed_challenge / forge_future
    source = Column(String(60), default="manual", nullable=False, index=True)
    source_id = Column(Integer, nullable=True, index=True)
    source_key = Column(String(120), nullable=True, index=True)

    # Reserved for the future connection to character growth.
    is_growth_task = Column(Boolean, default=False, nullable=False)

    moved_from_date = Column(Date, nullable=True)
    moved_to_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")


class MinimumDayTemplate(Base):
    __tablename__ = "minimum_day_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tasks = relationship("MinimumDayTemplateTask", back_populates="template", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_minimum_day_template_user_name"),
    )


class MinimumDayTemplateTask(Base):
    __tablename__ = "minimum_day_template_tasks"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("minimum_day_templates.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    template = relationship("MinimumDayTemplate", back_populates="tasks")


class DailyOsRecurrenceRule(Base):
    """Flexible calendar-style recurrence foundation.

    The UI will expose simple presets first, while the backend stores a JSON rule
    that can grow into full calendar behavior: selected weekdays, every X days,
    monthly nth weekday, until date, exceptions, ranges, and more.
    """

    __tablename__ = "daily_os_recurrence_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # minimum_day / planned_task_template / future_module
    target_type = Column(String(80), nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)

    # once / daily / weekdays / weekends / selected_weekdays / every_x_days /
    # weekly_interval / monthly / monthly_nth_weekday / date_range / custom
    rule_type = Column(String(80), nullable=False, index=True)
    rule_json = Column(JSON, default=dict, nullable=False)

    priority = Column(Integer, default=100, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    starts_on = Column(Date, nullable=True)
    ends_on = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)



class DailyOsInjectionLog(Base):
    """Prevents duplicate automatic injections for local calendar dates."""

    __tablename__ = "daily_os_injection_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    local_date = Column(Date, nullable=False, index=True)
    timezone = Column(String(80), nullable=False)

    source_type = Column(String(80), nullable=False, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    source_key = Column(String(180), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "local_date", "source_key", name="uq_daily_os_injection_user_date_source"),
    )
