from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class InsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    character_id: int
    threshold: int
    title: str
    content: str
    tags: list[Any]
    accepted: bool | None
    unlocked_at: datetime
    responded_at: datetime | None


class InsightRespondRequest(BaseModel):
    accepted: bool


class InsightRespondResponse(BaseModel):
    status: str
    insight: InsightResponse
    message: str


class InsightStatusResponse(BaseModel):
    status: str
    accepted_signal_count: int
    total_signal_count: int
    insight_threshold: int
    unlocked_count: int
    next_threshold: int
    signals_until_next_unlock: int
    unlock_available: bool
    latest_unlocked: InsightResponse | None
    unresponded_insights: list[InsightResponse]


class InsightListResponse(BaseModel):
    status: str
    insights: list[InsightResponse]
