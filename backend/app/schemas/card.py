from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    subtitle: str | None
    options: list[Any]
    tags: list[Any]
    signal_weights: dict[str, Any]
    visual_theme: str
    icon: str
    position: int
    is_onboarding: bool
    is_active: bool
    created_at: datetime


class CardStatsResponse(BaseModel):
    status: str
    total_cards: int
    onboarding_cards: int
    feed_cards: int
    expected_onboarding_cards: int
    onboarding_ready: bool
