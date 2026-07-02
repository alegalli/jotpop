from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DailyOsPageSummary(BaseModel):
    key: str
    title: str
    path: str
    description: str
    status: str


class RecurrenceRuleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_type: str
    target_id: int
    rule_type: str
    rule_json: dict[str, Any]
    label: str
    priority: int
    is_active: bool
    starts_on: date | None = None
    ends_on: date | None = None


class RecurrenceRuleCreateRequest(BaseModel):
    rule_type: Literal[
        "specific_date",
        "daily",
        "weekdays",
        "weekends",
        "selected_weekdays",
        "date_range",
        "every_x_days",
        "weekly_interval",
        "monthly",
        "monthly_nth_weekday",
        "default_always",
    ]
    rule_json: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=100, ge=1, le=5000)
    starts_on: date | None = None
    ends_on: date | None = None


class RecurrenceRuleUpdateRequest(BaseModel):
    rule_type: str | None = None
    rule_json: dict[str, Any] | None = None
    priority: int | None = Field(default=None, ge=1, le=5000)
    is_active: bool | None = None
    starts_on: date | None = None
    ends_on: date | None = None


class MinimumDayTemplateTaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    notes: str | None = None
    sort_order: int
    is_active: bool


class MinimumDayTemplateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    is_default: bool
    is_active: bool
    task_count: int
    tasks: list[MinimumDayTemplateTaskSummary]
    recurrence_rules: list[RecurrenceRuleSummary] = Field(default_factory=list)


class MinimumDayTemplateCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1500)


class MinimumDayTemplateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1500)


class MinimumDayTemplateTaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)


class MinimumDayTemplateTaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class MinimumDayPreviewItem(BaseModel):
    local_date: date
    weekday: str
    template_id: int
    template_name: str
    rule_label: str


class MinimumDayListResponse(BaseModel):
    timezone: str
    today: date
    active_template: MinimumDayTemplateSummary | None
    templates: list[MinimumDayTemplateSummary]
    preview: list[MinimumDayPreviewItem] = Field(default_factory=list)
    auto_injection: dict[str, Any]


class DailyTaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    notes: str | None = None
    task_date: date
    status: str
    source: str
    source_id: int | None = None
    source_key: str | None = None
    is_growth_task: bool
    moved_from_date: date | None = None
    moved_to_date: date | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime




class DailyOsDoneDaySummary(BaseModel):
    local_date: date
    weekday: str
    is_today: bool
    counts: dict[str, int]
    short_description: str
    tasks: list[DailyTaskSummary]


class DailyOsDoneResponse(BaseModel):
    timezone: str
    today: date
    last_7_days: list[DailyOsDoneDaySummary]
    totals: dict[str, int]
    older_strategy: dict[str, str]




class DailyOsQaCheck(BaseModel):
    key: str
    label: str
    status: Literal["pass", "warn", "fail"]
    detail: str


class DailyOsQaResponse(BaseModel):
    timezone: str
    today: date
    status: Literal["pass", "warn", "fail"]
    summary: dict[str, int]
    checks: list[DailyOsQaCheck]
    notes: list[str] = Field(default_factory=list)


class DailyTaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)
    task_date: date | None = None
    timezone: str = Field(default="UTC", max_length=80)
    source: str = Field(default="manual", max_length=60)


class DailyTaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)


class DailyTaskMoveRequest(BaseModel):
    task_date: date


class DailyTaskListResponse(BaseModel):
    timezone: str
    today: date
    tasks: list[DailyTaskSummary]
    counts: dict[str, int]
    minimum_day: MinimumDayTemplateSummary | None = None
    auto_injection: dict[str, Any] = Field(default_factory=dict)


class DailyTaskMoveResponse(BaseModel):
    moved_from: DailyTaskSummary
    moved_to: DailyTaskSummary


class DailyOsPlanResponse(BaseModel):
    timezone: str
    today: date
    tomorrow: date
    next_7_end: date
    tomorrow_tasks: list[DailyTaskSummary]
    next_7_days: list[DailyTaskSummary]
    later: list[DailyTaskSummary]
    counts: dict[str, int]


class DailyOsPageCounts(BaseModel):
    daily_tasks: int
    today_tasks: int
    minimum_day_templates: int
    minimum_day_tasks: int
    recurrence_rules: int
    injection_logs: int


class DailyOsStatusResponse(BaseModel):
    status: str
    timezone: str
    today: date
    app_midnight_rule: str
    pages: list[DailyOsPageSummary]
    default_minimum_day: MinimumDayTemplateSummary | None = None
    counts: dict[str, int]
    next_steps: list[str]


class TimezoneQuery(BaseModel):
    timezone: str = Field(default="UTC", max_length=80)
