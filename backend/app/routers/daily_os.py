from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.schemas.daily_os import (
    DailyOsDoneDaySummary,
    DailyOsDoneResponse,
    DailyOsPageSummary,
    DailyOsPlanResponse,
    DailyOsQaCheck,
    DailyOsQaResponse,
    DailyOsStatusResponse,
    DailyTaskCreateRequest,
    DailyTaskListResponse,
    DailyTaskMoveRequest,
    DailyTaskMoveResponse,
    DailyTaskSummary,
    DailyTaskUpdateRequest,
    MinimumDayListResponse,
    MinimumDayPreviewItem,
    MinimumDayTemplateCreateRequest,
    MinimumDayTemplateSummary,
    MinimumDayTemplateTaskCreateRequest,
    MinimumDayTemplateTaskSummary,
    MinimumDayTemplateTaskUpdateRequest,
    MinimumDayTemplateUpdateRequest,
    RecurrenceRuleCreateRequest,
    RecurrenceRuleSummary,
    RecurrenceRuleUpdateRequest,
)
from app.services.daily_os_service import (
    add_minimum_day_template_task,
    build_daily_os_pages,
    build_minimum_day_preview,
    complete_daily_task,
    create_daily_task,
    create_minimum_day_rule,
    create_minimum_day_template,
    delete_minimum_day_template_task,
    delete_recurrence_rule,
    drop_daily_task,
    ensure_default_minimum_day_template,
    get_applicable_minimum_day_template,
    get_daily_os_counts,
    hard_delete_daily_task,
    list_minimum_day_rules,
    list_done_history,
    list_minimum_day_templates,
    list_plan_sections,
    list_tasks_for_date,
    move_daily_task,
    recurrence_rule_label,
    run_daily_os_local_qa,
    sync_today_minimum_day_tasks,
    task_counts,
    today_in_timezone,
    update_daily_task,
    update_minimum_day_template,
    update_minimum_day_template_task,
    update_recurrence_rule,
)

router = APIRouter(prefix="/daily-os", tags=["daily-os"])


def serialize_recurrence_rule(rule) -> RecurrenceRuleSummary:
    return RecurrenceRuleSummary(
        id=rule.id,
        target_type=rule.target_type,
        target_id=rule.target_id,
        rule_type=rule.rule_type,
        rule_json=rule.rule_json or {},
        label=recurrence_rule_label(rule),
        priority=rule.priority,
        is_active=rule.is_active,
        starts_on=rule.starts_on,
        ends_on=rule.ends_on,
    )


def serialize_minimum_day(default_template, rules=None):
    rule_items = rules if rules is not None else []
    return MinimumDayTemplateSummary(
        id=default_template.id,
        name=default_template.name,
        description=default_template.description,
        is_default=default_template.is_default,
        is_active=default_template.is_active,
        task_count=len([task for task in default_template.tasks if task.is_active]),
        tasks=[
            MinimumDayTemplateTaskSummary.model_validate(task)
            for task in sorted(default_template.tasks, key=lambda item: item.sort_order)
            if task.is_active
        ],
        recurrence_rules=[serialize_recurrence_rule(rule) for rule in rule_items],
    )


def serialize_minimum_day_with_rules(db: Session, user: User, template):
    rules = list_minimum_day_rules(db, user, template.id)
    return serialize_minimum_day(template, rules=rules)


def injection_public_payload(sync_result: dict) -> dict:
    matched_rule = sync_result.get("matched_rule")
    return {
        "created_count": sync_result.get("created_count", 0),
        "already_synced": sync_result.get("already_synced", False),
        "source": "minimum_day",
        "rule_label": recurrence_rule_label(matched_rule) if matched_rule is not None else "Default fallback",
    }


@router.get("/status", response_model=DailyOsStatusResponse)
def daily_os_status(
    timezone: str = Query(default="UTC", max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyOsStatusResponse:
    today, safe_timezone = today_in_timezone(timezone)
    default_template = ensure_default_minimum_day_template(db, current_user)
    counts = get_daily_os_counts(db, current_user, today)

    return DailyOsStatusResponse(
        status="ok",
        timezone=safe_timezone,
        today=today,
        app_midnight_rule="Daily OS rolls over at midnight in the user's browser timezone.",
        pages=[DailyOsPageSummary(**page) for page in build_daily_os_pages()],
        default_minimum_day=serialize_minimum_day_with_rules(db, current_user, default_template),
        counts=counts,
        next_steps=[
            "Step 39: Integration and local QA.",
            "Step 40: Deploy Daily OS.",
        ],
    )


@router.get("/tasks/today", response_model=DailyTaskListResponse)
def get_today_tasks(
    timezone: str = Query(default="UTC", max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyTaskListResponse:
    sync_result = sync_today_minimum_day_tasks(db, current_user, timezone)
    today = sync_result["today"]
    safe_timezone = sync_result["timezone"]
    template = sync_result["template"]
    tasks = list_tasks_for_date(db, current_user, today)
    return DailyTaskListResponse(
        timezone=safe_timezone,
        today=today,
        tasks=[DailyTaskSummary.model_validate(task) for task in tasks],
        counts=task_counts(tasks),
        minimum_day=serialize_minimum_day_with_rules(db, current_user, template),
        auto_injection=injection_public_payload(sync_result),
    )


@router.get("/plan", response_model=DailyOsPlanResponse)
def get_plan(
    timezone: str = Query(default="UTC", max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyOsPlanResponse:
    today, safe_timezone = today_in_timezone(timezone)
    ensure_default_minimum_day_template(db, current_user)
    sections = list_plan_sections(db, current_user, today)
    all_tasks = sections["tomorrow_tasks"] + sections["next_7_days"] + sections["later"]
    return DailyOsPlanResponse(
        timezone=safe_timezone,
        today=today,
        tomorrow=sections["tomorrow"],
        next_7_end=sections["next_7_end"],
        tomorrow_tasks=[DailyTaskSummary.model_validate(task) for task in sections["tomorrow_tasks"]],
        next_7_days=[DailyTaskSummary.model_validate(task) for task in sections["next_7_days"]],
        later=[DailyTaskSummary.model_validate(task) for task in sections["later"]],
        counts=task_counts(all_tasks),
    )




@router.get("/done", response_model=DailyOsDoneResponse)
def get_done_history(
    timezone: str = Query(default="UTC", max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyOsDoneResponse:
    # Sync today first so Done reflects the current local day baseline if the user
    # opens the record before visiting Do it Today.
    sync_result = sync_today_minimum_day_tasks(db, current_user, timezone)
    today = sync_result["today"]
    safe_timezone = sync_result["timezone"]
    history = list_done_history(db, current_user, today, days=7)
    return DailyOsDoneResponse(
        timezone=safe_timezone,
        today=today,
        last_7_days=[
            DailyOsDoneDaySummary(
                local_date=item["local_date"],
                weekday=item["weekday"],
                is_today=item["is_today"],
                counts=item["counts"],
                short_description=item["short_description"],
                tasks=[DailyTaskSummary.model_validate(task) for task in item["tasks"]],
            )
            for item in history["last_7_days"]
        ],
        totals=history["totals"],
        older_strategy=history["older_strategy"],
    )


@router.get("/qa", response_model=DailyOsQaResponse)
def get_daily_os_qa(
    timezone: str = Query(default="UTC", max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyOsQaResponse:
    qa = run_daily_os_local_qa(db, current_user, timezone)
    return DailyOsQaResponse(
        timezone=qa["timezone"],
        today=qa["today"],
        status=qa["status"],
        summary=qa["summary"],
        checks=[DailyOsQaCheck(**item) for item in qa["checks"]],
        notes=qa["notes"],
    )


@router.get("/minimum-days", response_model=MinimumDayListResponse)
def get_minimum_days(
    timezone: str = Query(default="UTC", max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MinimumDayListResponse:
    today, safe_timezone = today_in_timezone(timezone)
    templates = list_minimum_day_templates(db, current_user)
    active_template = get_applicable_minimum_day_template(db, current_user, today)
    preview = build_minimum_day_preview(db, current_user, today, days=14)
    return MinimumDayListResponse(
        timezone=safe_timezone,
        today=today,
        active_template=serialize_minimum_day_with_rules(db, current_user, active_template),
        templates=[serialize_minimum_day_with_rules(db, current_user, template) for template in templates],
        preview=[MinimumDayPreviewItem(**item) for item in preview],
        auto_injection={
            "mode": "automatic",
            "already_synced": False,
            "created_count": 0,
            "message": "The active Minimum Day is injected automatically when Do it Today syncs.",
        },
    )


@router.post("/minimum-days", response_model=MinimumDayTemplateSummary, status_code=status.HTTP_201_CREATED)
def create_minimum_day(
    payload: MinimumDayTemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MinimumDayTemplateSummary:
    template = create_minimum_day_template(db, current_user, name=payload.name, description=payload.description)
    return serialize_minimum_day_with_rules(db, current_user, template)


@router.patch("/minimum-days/{template_id}", response_model=MinimumDayTemplateSummary)
def update_minimum_day(
    template_id: int,
    payload: MinimumDayTemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MinimumDayTemplateSummary:
    template = update_minimum_day_template(
        db,
        current_user,
        template_id,
        name=payload.name,
        description=payload.description,
    )
    return serialize_minimum_day_with_rules(db, current_user, template)


@router.post("/minimum-days/{template_id}/tasks", response_model=MinimumDayTemplateTaskSummary, status_code=status.HTTP_201_CREATED)
def create_minimum_day_task(
    template_id: int,
    payload: MinimumDayTemplateTaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MinimumDayTemplateTaskSummary:
    task = add_minimum_day_template_task(
        db,
        current_user,
        template_id,
        title=payload.title,
        notes=payload.notes,
    )
    return MinimumDayTemplateTaskSummary.model_validate(task)


@router.patch("/minimum-days/{template_id}/tasks/{task_id}", response_model=MinimumDayTemplateTaskSummary)
def update_minimum_day_task(
    template_id: int,
    task_id: int,
    payload: MinimumDayTemplateTaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MinimumDayTemplateTaskSummary:
    task = update_minimum_day_template_task(
        db,
        current_user,
        template_id,
        task_id,
        title=payload.title,
        notes=payload.notes,
        is_active=payload.is_active,
    )
    return MinimumDayTemplateTaskSummary.model_validate(task)


@router.delete("/minimum-days/{template_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_minimum_day_task(
    template_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_minimum_day_template_task(db, current_user, template_id, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/minimum-days/{template_id}/rules", response_model=RecurrenceRuleSummary, status_code=status.HTTP_201_CREATED)
def create_minimum_day_recurrence_rule(
    template_id: int,
    payload: RecurrenceRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurrenceRuleSummary:
    rule = create_minimum_day_rule(
        db,
        current_user,
        template_id,
        rule_type=payload.rule_type,
        rule_json=payload.rule_json,
        priority=payload.priority,
        starts_on=payload.starts_on,
        ends_on=payload.ends_on,
    )
    return serialize_recurrence_rule(rule)


@router.patch("/rules/{rule_id}", response_model=RecurrenceRuleSummary)
def patch_recurrence_rule(
    rule_id: int,
    payload: RecurrenceRuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurrenceRuleSummary:
    rule = update_recurrence_rule(
        db,
        current_user,
        rule_id,
        rule_type=payload.rule_type,
        rule_json=payload.rule_json,
        priority=payload.priority,
        is_active=payload.is_active,
        starts_on=payload.starts_on,
        ends_on=payload.ends_on,
    )
    return serialize_recurrence_rule(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recurrence_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_recurrence_rule(db, current_user, rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tasks", response_model=DailyTaskSummary, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: DailyTaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyTaskSummary:
    today, _ = today_in_timezone(payload.timezone)
    task = create_daily_task(
        db,
        current_user,
        title=payload.title,
        notes=payload.notes,
        task_date=payload.task_date or today,
        source=payload.source or "manual",
    )
    return DailyTaskSummary.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=DailyTaskSummary)
def update_task(
    task_id: int,
    payload: DailyTaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyTaskSummary:
    task = update_daily_task(db, current_user, task_id, title=payload.title, notes=payload.notes)
    return DailyTaskSummary.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=DailyTaskSummary)
def complete_task(
    task_id: int,
    timezone: str = Query(default="UTC", max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyTaskSummary:
    task = complete_daily_task(db, current_user, task_id, timezone)
    return DailyTaskSummary.model_validate(task)


@router.post("/tasks/{task_id}/drop", response_model=DailyTaskSummary)
def drop_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyTaskSummary:
    task = drop_daily_task(db, current_user, task_id)
    return DailyTaskSummary.model_validate(task)


@router.post("/tasks/{task_id}/move", response_model=DailyTaskMoveResponse)
def move_task(
    task_id: int,
    payload: DailyTaskMoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyTaskMoveResponse:
    moved_from, moved_to = move_daily_task(db, current_user, task_id, payload.task_date)
    return DailyTaskMoveResponse(
        moved_from=DailyTaskSummary.model_validate(moved_from),
        moved_to=DailyTaskSummary.model_validate(moved_to),
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    hard_delete_daily_task(db, current_user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
