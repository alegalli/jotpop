from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EvolutionCharacterSnapshot(BaseModel):
    id: int
    display_name: str
    current_state: str
    identity_label: str
    accepted_signal_count: int
    total_signal_count: int
    forge_state: str
    forge_days: int
    forge_cooling: bool
    today_alignment: int
    created_at: datetime


class EvolutionMetric(BaseModel):
    label: str
    value: str | int
    helper: str | None = None


class EvolutionAchievement(BaseModel):
    code: str
    title: str
    description: str
    icon: str
    unlocked: bool


class EvolutionInsightItem(BaseModel):
    id: int
    threshold: int
    title: str
    content: str
    tags: list[Any]
    accepted: bool | None
    unlocked_at: datetime
    responded_at: datetime | None


class EvolutionSummaryResponse(BaseModel):
    status: str
    title: str
    subtitle: str
    character: EvolutionCharacterSnapshot
    metrics: list[EvolutionMetric]
    unlocked_card_types: list[str]
    achievements: list[EvolutionAchievement]
    insights: list[EvolutionInsightItem]
    next_unlock: dict[str, Any]
