from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JotCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=140)
    prompt: str | None = Field(default=None, max_length=280)


class JotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    character_id: int
    card_id: int | None
    prompt: str | None
    content: str
    created_at: datetime


class JotSummaryResponse(BaseModel):
    status: str
    total_jots: int
    latest_jots: list[JotResponse]
    path_message: str


class JotCreateResponse(BaseModel):
    status: str
    jot: JotResponse
    total_jots: int
    path_message: str
