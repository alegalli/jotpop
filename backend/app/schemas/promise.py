from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PromiseTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    difficulty: str
    forge_points: int
    tags: list[Any]
    suggestion_weight: int
    is_active: bool
    created_at: datetime


class PromiseTemplateListResponse(BaseModel):
    status: str
    count: int
    templates: list[PromiseTemplateResponse]


class PromiseSuggestionResponse(BaseModel):
    status: str
    count: int
    required_selection_count: int
    note: str
    suggestions: list[PromiseTemplateResponse]


class DailyPromiseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    character_id: int
    template_id: int | None
    title: str
    difficulty: str
    forge_points: int
    selected_date: date
    is_system_proposed: bool
    is_locked: bool
    created_at: datetime
    completed: bool = False
    completed_at: datetime | None = None


class PromiseSelectionRequest(BaseModel):
    # Can be fewer than 3 when Feed challenges have already claimed
    # one or more of today's first 3 Promise slots.
    template_ids: list[int] = Field(default_factory=list, max_length=3)


class PromiseForgeRequest(BaseModel):
    proof_text: str | None = Field(default=None, max_length=500)


class TodayPromisesResponse(BaseModel):
    status: str
    selected_date: date
    required_selection_count: int
    selected_count: int
    completed_count: int
    is_locked: bool
    total_forge_points: int
    completed_forge_points: int
    alignment_percent: int
    alignment_label: str = "Unchosen"
    alignment_message: str = "Choose 3 Promises so Alignment can start."
    remaining_forge_points: int = 0
    alignment_question: str = "Did you do what mattered?"
    forge_threshold_points: int = 2
    forge_active_today: bool = False
    forge_points_needed_today: int = 2
    forge_days: int = 0
    forge_state: str = "Cold"
    forge_cooling: bool = False
    daily_promises: list[DailyPromiseResponse]


class PromiseSelectionResponse(BaseModel):
    status: str
    message: str
    selected_date: date
    required_selection_count: int
    selected_count: int
    completed_count: int
    is_locked: bool
    total_forge_points: int
    completed_forge_points: int
    alignment_percent: int
    alignment_label: str = "Unchosen"
    alignment_message: str = "Choose 3 Promises so Alignment can start."
    remaining_forge_points: int = 0
    alignment_question: str = "Did you do what mattered?"
    forge_threshold_points: int = 2
    forge_active_today: bool = False
    forge_points_needed_today: int = 2
    forge_days: int = 0
    forge_state: str = "Cold"
    forge_cooling: bool = False
    daily_promises: list[DailyPromiseResponse]


class PromiseForgeResponse(BaseModel):
    status: str
    message: str
    forged_promise: DailyPromiseResponse
    today: TodayPromisesResponse


class PromiseStatsResponse(BaseModel):
    status: str
    total_templates: int
    active_templates: int
    expected_minimum_templates: int
    templates_ready: bool
    difficulty_counts: dict[str, int]


class ForgeStatusResponse(BaseModel):
    status: str
    forge_threshold_points: int
    forge_active_today: bool
    forge_points_needed_today: int
    forge_days: int
    forge_state: str
    forge_cooling: bool
    today_alignment: int
    selected_count: int
    completed_count: int
    total_forge_points: int
    completed_forge_points: int
    note: str


class AlignmentStatusResponse(BaseModel):
    status: str
    selected_date: date
    question: str
    alignment_percent: int
    alignment_label: str
    alignment_message: str
    selected_count: int
    completed_count: int
    total_forge_points: int
    completed_forge_points: int
    remaining_forge_points: int
    forge_active_today: bool
    forge_state: str
    forge_days: int
    incomplete_promises: list[DailyPromiseResponse]
    note: str
