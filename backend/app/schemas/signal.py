from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import CharacterResponse


class TemporarySignalImportItem(BaseModel):
    temporary_id: str | None = None
    card_id: int
    card_type: str | None = None
    card_title: str | None = None
    choice: str
    direction: str = "tap"
    accepted: bool = True
    tags: list[str] = Field(default_factory=list)
    signal_weights: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class SignalImportRequest(BaseModel):
    signals: list[TemporarySignalImportItem] = Field(default_factory=list, max_length=50)


class CardSignalCreateRequest(BaseModel):
    card_id: int
    choice: str | None = None
    direction: str = "tap"
    accepted: bool = True
    jot_text: str | None = Field(default=None, max_length=140)


class SignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    character_id: int
    card_interaction_id: int | None
    source: str
    action: str
    accepted: bool
    tags: list[Any]
    weights: dict[str, Any]
    created_at: datetime


class SignalImportResponse(BaseModel):
    status: str
    imported: int
    skipped: int
    accepted_imported: int
    total_signal_count: int
    accepted_signal_count: int
    character: CharacterResponse


class SignalCreateResponse(BaseModel):
    status: str
    signal: SignalResponse
    total_signal_count: int
    accepted_signal_count: int
    character: CharacterResponse


class SignalSummaryResponse(BaseModel):
    status: str
    total_signal_count: int
    accepted_signal_count: int
    latest_signals: list[SignalResponse]
