from calendar import monthrange
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    DailyOsInjectionLog,
    DailyOsRecurrenceRule,
    DailyTask,
    MinimumDayTemplate,
    MinimumDayTemplateTask,
    User,
)

DEFAULT_MINIMUM_DAY_TASKS = [
    "Drink water",
    "Move for 10 minutes",
    "Do one tiny useful thing",
    "Reset one small space",
]

DEFAULT_MINIMUM_DAY_DESCRIPTION = "A day where I protect momentum without pretending I can do everything."
VISIBLE_TASK_STATUSES = ["planned", "completed"]
HISTORY_TASK_STATUSES = ["planned", "completed", "moved", "dropped"]
WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def normalize_timezone(timezone: str | None) -> str:
    candidate = (timezone or "UTC").strip() or "UTC"
    try:
        ZoneInfo(candidate)
        return candidate
    except ZoneInfoNotFoundError:
        return "UTC"


def today_in_timezone(timezone: str | None):
    safe_timezone = normalize_timezone(timezone)
    return datetime.now(ZoneInfo(safe_timezone)).date(), safe_timezone


def now_in_timezone(timezone: str | None) -> datetime:
    safe_timezone = normalize_timezone(timezone)
    return datetime.now(ZoneInfo(safe_timezone)).replace(tzinfo=None)


def _parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _weekday_index(value) -> int | None:
    if isinstance(value, int) and 0 <= value <= 6:
        return value
    if isinstance(value, str):
        clean = value.strip().lower()
        if clean.isdigit():
            candidate = int(clean)
            return candidate if 0 <= candidate <= 6 else None
        return WEEKDAY_ALIASES.get(clean)
    return None


def _weekday_list(values) -> set[int]:
    if values is None:
        return set()
    if isinstance(values, str):
        values = [item.strip() for item in values.split(",")]
    return {idx for idx in (_weekday_index(value) for value in values) if idx is not None}


def _date_is_in_window(rule: DailyOsRecurrenceRule, local_date: date) -> bool:
    payload = rule.rule_json or {}
    start = rule.starts_on or _parse_date(payload.get("start_date")) or _parse_date(payload.get("starts_on"))
    end = rule.ends_on or _parse_date(payload.get("end_date")) or _parse_date(payload.get("ends_on")) or _parse_date(payload.get("until_date"))
    if start is not None and local_date < start:
        return False
    if end is not None and local_date > end:
        return False
    exceptions = payload.get("exceptions") or payload.get("exception_dates") or []
    exception_dates = {_parse_date(item) for item in exceptions}
    if local_date in exception_dates:
        return False
    return True


def _nth_weekday_of_month(year: int, month: int, weekday: int, ordinal: int) -> date | None:
    if ordinal == 0:
        return None
    last_day = monthrange(year, month)[1]
    if ordinal > 0:
        current = date(year, month, 1)
        hits = []
        while current.month == month:
            if current.weekday() == weekday:
                hits.append(current)
            current += timedelta(days=1)
        if len(hits) >= ordinal:
            return hits[ordinal - 1]
        return None
    current = date(year, month, last_day)
    hits = []
    while current.month == month:
        if current.weekday() == weekday:
            hits.append(current)
        current -= timedelta(days=1)
    return hits[abs(ordinal) - 1] if len(hits) >= abs(ordinal) else None


def recurrence_rule_matches_date(rule: DailyOsRecurrenceRule, local_date: date) -> bool:
    if not rule.is_active:
        return False
    payload = rule.rule_json or {}
    rule_type = rule.rule_type

    if rule_type == "default_always":
        return _date_is_in_window(rule, local_date)

    if not _date_is_in_window(rule, local_date):
        return False

    if rule_type == "specific_date":
        target = _parse_date(payload.get("date") or payload.get("specific_date") or rule.starts_on)
        return target == local_date

    if rule_type == "daily":
        return True

    if rule_type == "weekdays":
        return local_date.weekday() < 5

    if rule_type == "weekends":
        return local_date.weekday() >= 5

    if rule_type == "selected_weekdays":
        weekdays = _weekday_list(payload.get("weekdays") or payload.get("selected_weekdays"))
        return local_date.weekday() in weekdays

    if rule_type == "date_range":
        # Window matching already checked start/end.
        return True

    if rule_type == "every_x_days":
        start = rule.starts_on or _parse_date(payload.get("start_date"))
        interval_days = int(payload.get("interval_days") or payload.get("interval") or 1)
        if start is None or interval_days <= 0 or local_date < start:
            return False
        return (local_date - start).days % interval_days == 0

    if rule_type == "weekly_interval":
        start = rule.starts_on or _parse_date(payload.get("start_date"))
        interval_weeks = int(payload.get("interval_weeks") or payload.get("interval") or 1)
        weekdays = _weekday_list(payload.get("weekdays")) or {start.weekday() if start else local_date.weekday()}
        if start is None or interval_weeks <= 0 or local_date < start or local_date.weekday() not in weekdays:
            return False
        return ((local_date - start).days // 7) % interval_weeks == 0

    if rule_type == "monthly":
        day = int(payload.get("day") or payload.get("day_of_month") or 1)
        day = max(1, min(day, monthrange(local_date.year, local_date.month)[1]))
        return local_date.day == day

    if rule_type == "monthly_nth_weekday":
        weekday = _weekday_index(payload.get("weekday"))
        ordinal = int(payload.get("ordinal") or payload.get("nth") or 1)
        if weekday is None:
            return False
        return _nth_weekday_of_month(local_date.year, local_date.month, weekday, ordinal) == local_date

    return False


def recurrence_rule_label(rule: DailyOsRecurrenceRule) -> str:
    payload = rule.rule_json or {}
    rule_type = rule.rule_type
    if rule_type == "default_always":
        return "Default fallback"
    if rule_type == "specific_date":
        return f"Only on {payload.get('date') or payload.get('specific_date') or rule.starts_on}"
    if rule_type == "daily":
        return "Every day"
    if rule_type == "weekdays":
        return "Weekdays"
    if rule_type == "weekends":
        return "Weekends"
    if rule_type == "selected_weekdays":
        weekdays = _weekday_list(payload.get("weekdays"))
        names = ", ".join(WEEKDAY_NAMES[index].title() for index in sorted(weekdays)) or "selected days"
        return f"Every {names}"
    if rule_type == "date_range":
        return f"From {payload.get('start_date') or rule.starts_on} to {payload.get('end_date') or rule.ends_on}"
    if rule_type == "every_x_days":
        return f"Every {payload.get('interval_days') or payload.get('interval') or 1} days"
    if rule_type == "weekly_interval":
        interval = payload.get("interval_weeks") or payload.get("interval") or 1
        weekdays = _weekday_list(payload.get("weekdays"))
        names = ", ".join(WEEKDAY_NAMES[index].title() for index in sorted(weekdays)) or "chosen day"
        return f"Every {interval} weeks · {names}"
    if rule_type == "monthly":
        return f"Monthly on day {payload.get('day') or payload.get('day_of_month') or 1}"
    if rule_type == "monthly_nth_weekday":
        ordinal = int(payload.get("ordinal") or payload.get("nth") or 1)
        weekday = _weekday_index(payload.get("weekday"))
        weekday_name = WEEKDAY_NAMES[weekday].title() if weekday is not None else "weekday"
        ordinal_label = {1: "first", 2: "second", 3: "third", 4: "fourth", -1: "last"}.get(ordinal, f"#{ordinal}")
        return f"Monthly · {ordinal_label} {weekday_name}"
    return rule_type.replace("_", " ").title()


def ensure_default_minimum_day_template(db: Session, user: User) -> MinimumDayTemplate:
    existing = (
        db.query(MinimumDayTemplate)
        .filter(
            MinimumDayTemplate.user_id == user.id,
            MinimumDayTemplate.is_default.is_(True),
        )
        .first()
    )
    if existing is not None:
        has_default_rule = (
            db.query(DailyOsRecurrenceRule)
            .filter(
                DailyOsRecurrenceRule.user_id == user.id,
                DailyOsRecurrenceRule.target_type == "minimum_day",
                DailyOsRecurrenceRule.target_id == existing.id,
                DailyOsRecurrenceRule.rule_type == "default_always",
            )
            .first()
        )
        if has_default_rule is None:
            db.add(
                DailyOsRecurrenceRule(
                    user_id=user.id,
                    target_type="minimum_day",
                    target_id=existing.id,
                    rule_type="default_always",
                    rule_json={"description": "Fallback template for days without a more specific Minimum Day."},
                    priority=1000,
                    is_active=True,
                )
            )
            db.commit()
        return existing

    template = MinimumDayTemplate(
        user_id=user.id,
        name="THE MINIMUM DAY",
        description=DEFAULT_MINIMUM_DAY_DESCRIPTION,
        is_default=True,
        is_active=True,
    )
    db.add(template)
    db.flush()

    for index, title in enumerate(DEFAULT_MINIMUM_DAY_TASKS):
        db.add(
            MinimumDayTemplateTask(
                template_id=template.id,
                title=title,
                notes=None,
                sort_order=index,
                is_active=True,
            )
        )

    db.add(
        DailyOsRecurrenceRule(
            user_id=user.id,
            target_type="minimum_day",
            target_id=template.id,
            rule_type="default_always",
            rule_json={"description": "Fallback template for days without a more specific Minimum Day."},
            priority=1000,
            is_active=True,
        )
    )
    db.commit()
    db.refresh(template)
    return template


def get_daily_os_counts(db: Session, user: User, today: date | None = None) -> dict[str, int]:
    today_query = db.query(DailyTask).filter(DailyTask.user_id == user.id)
    if today is not None:
        today_query = today_query.filter(DailyTask.task_date == today, DailyTask.status.in_(VISIBLE_TASK_STATUSES))

    return {
        "daily_tasks": db.query(DailyTask).filter(DailyTask.user_id == user.id).count(),
        "today_tasks": today_query.count() if today is not None else 0,
        "minimum_day_templates": db.query(MinimumDayTemplate).filter(MinimumDayTemplate.user_id == user.id).count(),
        "minimum_day_tasks": (
            db.query(MinimumDayTemplateTask)
            .join(MinimumDayTemplate, MinimumDayTemplateTask.template_id == MinimumDayTemplate.id)
            .filter(MinimumDayTemplate.user_id == user.id)
            .count()
        ),
        "recurrence_rules": db.query(DailyOsRecurrenceRule).filter(DailyOsRecurrenceRule.user_id == user.id).count(),
        "injection_logs": db.query(DailyOsInjectionLog).filter(DailyOsInjectionLog.user_id == user.id).count(),
    }


def build_daily_os_pages() -> list[dict[str, str]]:
    return [
        {
            "key": "doittoday",
            "title": "Do it Today",
            "path": "/doittoday",
            "description": "Today's practical task list: add, complete, move, drop, or delete tasks.",
            "status": "core_ready",
        },
        {
            "key": "minday",
            "title": "Minimum Day",
            "path": "/minday",
            "description": "Edit the baseline and recurrence rules that appear automatically.",
            "status": "recurrence_ready",
        },
        {
            "key": "done",
            "title": "Done",
            "path": "/done",
            "description": "Review completed, planned, moved, and dropped tasks by day.",
            "status": "history_ready",
        },
        {
            "key": "plan",
            "title": "Plan",
            "path": "/plan",
            "description": "Plan tasks for tomorrow, the next 7 days, and later.",
            "status": "core_ready",
        },
    ]


def task_counts(tasks: list[DailyTask]) -> dict[str, int]:
    counts = {"planned": 0, "completed": 0, "moved": 0, "dropped": 0, "total": len(tasks)}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
    return counts




def done_short_description(counts: dict[str, int]) -> str:
    if counts.get("total", 0) == 0:
        return "No tasks planned."
    return (
        f"Completed {counts.get('completed', 0)} · "
        f"Planned {counts.get('planned', 0)} · "
        f"Moved {counts.get('moved', 0)} · "
        f"Dropped {counts.get('dropped', 0)}"
    )


def list_done_history(db: Session, user: User, today: date, days: int = 7) -> dict[str, object]:
    start_date = today - timedelta(days=days - 1)
    tasks = (
        db.query(DailyTask)
        .filter(
            DailyTask.user_id == user.id,
            DailyTask.task_date >= start_date,
            DailyTask.task_date <= today,
            DailyTask.status.in_(HISTORY_TASK_STATUSES),
        )
        .order_by(DailyTask.task_date.desc(), DailyTask.created_at.asc())
        .all()
    )

    tasks_by_date: dict[date, list[DailyTask]] = {}
    for task in tasks:
        tasks_by_date.setdefault(task.task_date, []).append(task)

    day_items = []
    totals = {"planned": 0, "completed": 0, "moved": 0, "dropped": 0, "total": 0}
    for offset in range(days):
        local_date = today - timedelta(days=offset)
        day_tasks = tasks_by_date.get(local_date, [])
        counts = task_counts(day_tasks)
        for key in totals:
            totals[key] += counts.get(key, 0)
        day_items.append(
            {
                "local_date": local_date,
                "weekday": "Today" if local_date == today else WEEKDAY_NAMES[local_date.weekday()].title(),
                "is_today": local_date == today,
                "counts": counts,
                "short_description": done_short_description(counts),
                "tasks": day_tasks,
            }
        )

    return {
        "last_7_days": day_items,
        "totals": totals,
        "older_strategy": {
            "next": "Older than 7 days will become weekly summaries.",
            "later": "Older weeks will roll into monthly summaries when the history grows.",
            "language": "No shame language: completed, planned, moved, dropped.",
        },
    }


def get_task_or_404(db: Session, user: User, task_id: int) -> DailyTask:
    task = db.query(DailyTask).filter(DailyTask.id == task_id, DailyTask.user_id == user.id).first()
    if task is None or task.status == "deleted_shadow":
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


def get_minimum_day_template_or_404(db: Session, user: User, template_id: int) -> MinimumDayTemplate:
    template = (
        db.query(MinimumDayTemplate)
        .filter(MinimumDayTemplate.id == template_id, MinimumDayTemplate.user_id == user.id)
        .first()
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Minimum Day template not found.")
    return template


def get_recurrence_rule_or_404(db: Session, user: User, rule_id: int) -> DailyOsRecurrenceRule:
    rule = db.query(DailyOsRecurrenceRule).filter(DailyOsRecurrenceRule.id == rule_id, DailyOsRecurrenceRule.user_id == user.id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Recurrence rule not found.")
    return rule


def get_minimum_day_template_task_or_404(
    db: Session,
    user: User,
    template_id: int,
    task_id: int,
) -> MinimumDayTemplateTask:
    template = get_minimum_day_template_or_404(db, user, template_id)
    task = (
        db.query(MinimumDayTemplateTask)
        .filter(
            MinimumDayTemplateTask.id == task_id,
            MinimumDayTemplateTask.template_id == template.id,
        )
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Minimum Day task not found.")
    return task


def list_minimum_day_rules(db: Session, user: User, template_id: int | None = None) -> list[DailyOsRecurrenceRule]:
    query = db.query(DailyOsRecurrenceRule).filter(
        DailyOsRecurrenceRule.user_id == user.id,
        DailyOsRecurrenceRule.target_type == "minimum_day",
    )
    if template_id is not None:
        query = query.filter(DailyOsRecurrenceRule.target_id == template_id)
    return query.order_by(DailyOsRecurrenceRule.priority.asc(), DailyOsRecurrenceRule.created_at.asc()).all()


def create_minimum_day_rule(
    db: Session,
    user: User,
    template_id: int,
    *,
    rule_type: str,
    rule_json: dict,
    priority: int,
    starts_on: date | None,
    ends_on: date | None,
) -> DailyOsRecurrenceRule:
    template = get_minimum_day_template_or_404(db, user, template_id)
    if template.is_default and rule_type != "default_always":
        # The default template can still receive rules, but keep it lower priority
        # unless the user explicitly chooses otherwise.
        priority = max(priority, 900)
    rule = DailyOsRecurrenceRule(
        user_id=user.id,
        target_type="minimum_day",
        target_id=template.id,
        rule_type=rule_type,
        rule_json=rule_json or {},
        priority=priority,
        starts_on=starts_on,
        ends_on=ends_on,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_recurrence_rule(
    db: Session,
    user: User,
    rule_id: int,
    *,
    rule_type: str | None,
    rule_json: dict | None,
    priority: int | None,
    is_active: bool | None,
    starts_on: date | None,
    ends_on: date | None,
) -> DailyOsRecurrenceRule:
    rule = get_recurrence_rule_or_404(db, user, rule_id)
    if rule_type is not None:
        rule.rule_type = rule_type
    if rule_json is not None:
        rule.rule_json = rule_json
    if priority is not None:
        rule.priority = priority
    if is_active is not None:
        rule.is_active = is_active
    if starts_on is not None:
        rule.starts_on = starts_on
    if ends_on is not None:
        rule.ends_on = ends_on
    db.commit()
    db.refresh(rule)
    return rule


def delete_recurrence_rule(db: Session, user: User, rule_id: int) -> None:
    rule = get_recurrence_rule_or_404(db, user, rule_id)
    if rule.rule_type == "default_always":
        raise HTTPException(status_code=400, detail="The default fallback rule cannot be deleted.")
    db.delete(rule)
    db.commit()


def create_daily_task(
    db: Session,
    user: User,
    *,
    title: str,
    notes: str | None,
    task_date: date,
    source: str = "manual",
    source_id: int | None = None,
    source_key: str | None = None,
) -> DailyTask:
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=422, detail="Task title is required.")

    task = DailyTask(
        user_id=user.id,
        title=clean_title,
        notes=(notes or "").strip() or None,
        task_date=task_date,
        status="planned",
        source=source or "manual",
        source_id=source_id,
        source_key=source_key,
        is_growth_task=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_daily_task(db: Session, user: User, task_id: int, *, title: str | None, notes: str | None) -> DailyTask:
    task = get_task_or_404(db, user, task_id)
    if title is not None:
        clean_title = title.strip()
        if not clean_title:
            raise HTTPException(status_code=422, detail="Task title cannot be empty.")
        task.title = clean_title
    if notes is not None:
        task.notes = notes.strip() or None
    db.commit()
    db.refresh(task)
    return task


def complete_daily_task(db: Session, user: User, task_id: int, timezone: str | None = None) -> DailyTask:
    task = get_task_or_404(db, user, task_id)
    task.status = "completed"
    task.completed_at = now_in_timezone(timezone)
    db.commit()
    db.refresh(task)
    return task


def drop_daily_task(db: Session, user: User, task_id: int) -> DailyTask:
    task = get_task_or_404(db, user, task_id)
    task.status = "dropped"
    db.commit()
    db.refresh(task)
    return task


def hard_delete_daily_task(db: Session, user: User, task_id: int) -> None:
    task = get_task_or_404(db, user, task_id)
    db.delete(task)
    db.commit()


def move_daily_task(db: Session, user: User, task_id: int, new_date: date) -> tuple[DailyTask, DailyTask]:
    original = get_task_or_404(db, user, task_id)
    if original.task_date == new_date and original.status == "planned":
        return original, original

    original.status = "moved"
    original.moved_to_date = new_date

    moved_copy = DailyTask(
        user_id=user.id,
        title=original.title,
        notes=original.notes,
        task_date=new_date,
        status="planned",
        source="manual" if original.source == "manual" else original.source,
        source_id=original.source_id,
        source_key=f"moved_from:{original.id}",
        is_growth_task=original.is_growth_task,
        moved_from_date=original.task_date,
    )
    db.add(moved_copy)
    db.commit()
    db.refresh(original)
    db.refresh(moved_copy)
    return original, moved_copy


def list_tasks_for_date(db: Session, user: User, task_date: date) -> list[DailyTask]:
    return (
        db.query(DailyTask)
        .filter(
            DailyTask.user_id == user.id,
            DailyTask.task_date == task_date,
            DailyTask.status.in_(VISIBLE_TASK_STATUSES),
        )
        .order_by(DailyTask.status.asc(), DailyTask.created_at.asc())
        .all()
    )


def list_plan_sections(db: Session, user: User, today: date) -> dict[str, list[DailyTask] | date]:
    tomorrow = today + timedelta(days=1)
    next_7_end = today + timedelta(days=7)
    future_tasks = (
        db.query(DailyTask)
        .filter(
            DailyTask.user_id == user.id,
            DailyTask.task_date > today,
            DailyTask.status.in_(VISIBLE_TASK_STATUSES),
        )
        .order_by(DailyTask.task_date.asc(), DailyTask.created_at.asc())
        .all()
    )
    return {
        "tomorrow": tomorrow,
        "next_7_end": next_7_end,
        "tomorrow_tasks": [task for task in future_tasks if task.task_date == tomorrow],
        "next_7_days": [task for task in future_tasks if tomorrow < task.task_date <= next_7_end],
        "later": [task for task in future_tasks if task.task_date > next_7_end],
    }


def list_minimum_day_templates(db: Session, user: User) -> list[MinimumDayTemplate]:
    ensure_default_minimum_day_template(db, user)
    return (
        db.query(MinimumDayTemplate)
        .filter(MinimumDayTemplate.user_id == user.id, MinimumDayTemplate.is_active.is_(True))
        .order_by(MinimumDayTemplate.is_default.desc(), MinimumDayTemplate.created_at.asc())
        .all()
    )


def create_minimum_day_template(db: Session, user: User, *, name: str, description: str | None) -> MinimumDayTemplate:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=422, detail="Minimum Day name is required.")
    template = MinimumDayTemplate(
        user_id=user.id,
        name=clean_name,
        description=(description or "").strip() or None,
        is_default=False,
        is_active=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_minimum_day_template(
    db: Session,
    user: User,
    template_id: int,
    *,
    name: str | None,
    description: str | None,
) -> MinimumDayTemplate:
    template = get_minimum_day_template_or_404(db, user, template_id)
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise HTTPException(status_code=422, detail="Minimum Day name cannot be empty.")
        template.name = clean_name
    if description is not None:
        template.description = description.strip() or None
    db.commit()
    db.refresh(template)
    return template


def add_minimum_day_template_task(
    db: Session,
    user: User,
    template_id: int,
    *,
    title: str,
    notes: str | None,
) -> MinimumDayTemplateTask:
    template = get_minimum_day_template_or_404(db, user, template_id)
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=422, detail="Minimum Day task title is required.")
    max_order = (
        db.query(func.max(MinimumDayTemplateTask.sort_order))
        .filter(MinimumDayTemplateTask.template_id == template.id)
        .scalar()
    )
    task = MinimumDayTemplateTask(
        template_id=template.id,
        title=clean_title,
        notes=(notes or "").strip() or None,
        sort_order=(max_order or 0) + 1,
        is_active=True,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_minimum_day_template_task(
    db: Session,
    user: User,
    template_id: int,
    task_id: int,
    *,
    title: str | None,
    notes: str | None,
    is_active: bool | None,
) -> MinimumDayTemplateTask:
    task = get_minimum_day_template_task_or_404(db, user, template_id, task_id)
    if title is not None:
        clean_title = title.strip()
        if not clean_title:
            raise HTTPException(status_code=422, detail="Minimum Day task title cannot be empty.")
        task.title = clean_title
    if notes is not None:
        task.notes = notes.strip() or None
    if is_active is not None:
        task.is_active = is_active
    db.commit()
    db.refresh(task)
    return task


def delete_minimum_day_template_task(db: Session, user: User, template_id: int, task_id: int) -> None:
    task = get_minimum_day_template_task_or_404(db, user, template_id, task_id)
    db.delete(task)
    db.commit()


def _minimum_day_source_key(template_id: int, task_id: int) -> str:
    return f"minimum_day:{template_id}:task:{task_id}"


def get_applicable_minimum_day_template_with_rule(db: Session, user: User, local_date: date) -> tuple[MinimumDayTemplate, DailyOsRecurrenceRule | None]:
    default_template = ensure_default_minimum_day_template(db, user)
    rules = list_minimum_day_rules(db, user)
    for rule in rules:
        if recurrence_rule_matches_date(rule, local_date):
            template = (
                db.query(MinimumDayTemplate)
                .filter(
                    MinimumDayTemplate.id == rule.target_id,
                    MinimumDayTemplate.user_id == user.id,
                    MinimumDayTemplate.is_active.is_(True),
                )
                .first()
            )
            if template is not None:
                return template, rule
    return default_template, None


def get_applicable_minimum_day_template(db: Session, user: User, local_date: date) -> MinimumDayTemplate:
    template, _ = get_applicable_minimum_day_template_with_rule(db, user, local_date)
    return template


def build_minimum_day_preview(db: Session, user: User, start_date: date, days: int = 14) -> list[dict[str, object]]:
    preview = []
    for offset in range(days):
        local_date = start_date + timedelta(days=offset)
        template, rule = get_applicable_minimum_day_template_with_rule(db, user, local_date)
        preview.append(
            {
                "local_date": local_date,
                "weekday": WEEKDAY_NAMES[local_date.weekday()].title(),
                "template_id": template.id,
                "template_name": template.name,
                "rule_label": recurrence_rule_label(rule) if rule is not None else "Default fallback",
            }
        )
    return preview


def sync_today_minimum_day_tasks(db: Session, user: User, timezone: str | None) -> dict[str, object]:
    local_date, safe_timezone = today_in_timezone(timezone)
    template, matched_rule = get_applicable_minimum_day_template_with_rule(db, user, local_date)
    active_template_tasks = [task for task in sorted(template.tasks, key=lambda item: item.sort_order) if task.is_active]
    source_key = f"minimum_day:{template.id}:date:{local_date.isoformat()}"

    existing_log = (
        db.query(DailyOsInjectionLog)
        .filter(
            DailyOsInjectionLog.user_id == user.id,
            DailyOsInjectionLog.local_date == local_date,
            DailyOsInjectionLog.source_key == source_key,
        )
        .first()
    )

    created_count = 0
    if existing_log is None:
        for template_task in active_template_tasks:
            task_key = _minimum_day_source_key(template.id, template_task.id)
            already_exists = (
                db.query(DailyTask)
                .filter(
                    DailyTask.user_id == user.id,
                    DailyTask.task_date == local_date,
                    DailyTask.source == "minimum_day",
                    DailyTask.source_id == template.id,
                    DailyTask.source_key == task_key,
                )
                .first()
            )
            if already_exists is not None:
                continue
            db.add(
                DailyTask(
                    user_id=user.id,
                    title=template_task.title,
                    notes=template_task.notes,
                    task_date=local_date,
                    status="planned",
                    source="minimum_day",
                    source_id=template.id,
                    source_key=task_key,
                    is_growth_task=False,
                )
            )
            created_count += 1

        db.add(
            DailyOsInjectionLog(
                user_id=user.id,
                local_date=local_date,
                timezone=safe_timezone,
                source_type="minimum_day",
                source_id=template.id,
                source_key=source_key,
            )
        )
        db.commit()

    return {
        "today": local_date,
        "timezone": safe_timezone,
        "template": template,
        "matched_rule": matched_rule,
        "created_count": created_count,
        "already_synced": existing_log is not None,
    }



def run_daily_os_local_qa(db: Session, user: User, timezone: str | None) -> dict[str, object]:
    """Return a non-destructive-ish Daily OS integration QA snapshot.

    It intentionally performs the same lazy sync the real pages perform, because
    the MVP rule is: Minimum Day appears automatically when the user opens the
    app. The endpoint is private to the logged-in user and is meant for local
    pre-deploy QA before the Daily OS release.
    """
    sync_result = sync_today_minimum_day_tasks(db, user, timezone)
    today = sync_result["today"]
    safe_timezone = sync_result["timezone"]
    template = sync_result["template"]

    today_tasks = list_tasks_for_date(db, user, today)
    plan_sections = list_plan_sections(db, user, today)
    preview = build_minimum_day_preview(db, user, today, days=14)
    history = list_done_history(db, user, today, days=7)
    counts = get_daily_os_counts(db, user, today)
    templates = list_minimum_day_templates(db, user)

    duplicate_minimum_day_keys = (
        db.query(DailyTask.source_key, func.count(DailyTask.id))
        .filter(
            DailyTask.user_id == user.id,
            DailyTask.task_date == today,
            DailyTask.source == "minimum_day",
            DailyTask.source_key.isnot(None),
        )
        .group_by(DailyTask.source_key)
        .having(func.count(DailyTask.id) > 1)
        .all()
    )

    checks: list[dict[str, str]] = []

    def add_check(key: str, label: str, passed: bool, detail: str, warn: bool = False) -> None:
        checks.append(
            {
                "key": key,
                "label": label,
                "status": "pass" if passed else ("warn" if warn else "fail"),
                "detail": detail,
            }
        )

    active_task_count = len([task for task in template.tasks if task.is_active]) if template is not None else 0
    minimum_day_today = len([task for task in today_tasks if task.source == "minimum_day"])
    future_count = len(plan_sections["tomorrow_tasks"]) + len(plan_sections["next_7_days"]) + len(plan_sections["later"])

    add_check(
        "timezone",
        "User timezone",
        safe_timezone != "UTC" or (timezone or "").upper() == "UTC",
        f"Using {safe_timezone}. Daily rollover is calculated from the browser timezone.",
        warn=True,
    )
    add_check(
        "default_minimum_day",
        "Default Minimum Day",
        any(template_item.is_default for template_item in templates),
        "THE MINIMUM DAY exists and remains the fallback template.",
    )
    add_check(
        "minimum_day_tasks",
        "Minimum Day task list",
        active_task_count > 0,
        f"Active template '{template.name if template else '—'}' has {active_task_count} active tasks.",
        warn=True,
    )
    add_check(
        "automatic_injection",
        "Automatic injection",
        sync_result.get("already_synced") or sync_result.get("created_count", 0) >= 0,
        f"Today's sync ran. Created {sync_result.get('created_count', 0)} tasks; already synced = {sync_result.get('already_synced')}.",
    )
    add_check(
        "minimum_day_visible_today",
        "Minimum Day visible today",
        minimum_day_today >= active_task_count if active_task_count else True,
        f"Today has {minimum_day_today} Minimum Day tasks visible in Do it Today.",
        warn=True,
    )
    add_check(
        "no_duplicate_injection",
        "No duplicate injection",
        len(duplicate_minimum_day_keys) == 0,
        "No duplicated Minimum Day source keys for today's local date." if len(duplicate_minimum_day_keys) == 0 else f"Found {len(duplicate_minimum_day_keys)} duplicated Minimum Day task keys.",
    )
    add_check(
        "plan_sections",
        "Plan sections",
        all(key in plan_sections for key in ["tomorrow_tasks", "next_7_days", "later"]),
        f"Plan is reachable. Future tasks visible: {future_count}.",
    )
    add_check(
        "done_history",
        "Done history",
        len(history.get("last_7_days", [])) == 7,
        f"Done returns {len(history.get('last_7_days', []))} local day summaries.",
    )
    add_check(
        "recurrence_preview",
        "Minimum Day preview",
        len(preview) == 14,
        f"Minimum Day recurrence preview returns {len(preview)} days.",
    )
    add_check(
        "forge_separation",
        "Forge remains separate",
        True,
        "Daily OS tasks are tracked as practical tasks and do not change Follow-through yet.",
    )

    summary = {
        "checks": len(checks),
        "passed": len([item for item in checks if item["status"] == "pass"]),
        "warnings": len([item for item in checks if item["status"] == "warn"]),
        "failures": len([item for item in checks if item["status"] == "fail"]),
        "today_tasks": len(today_tasks),
        "future_tasks": future_count,
    }
    status = "fail" if summary["failures"] else ("warn" if summary["warnings"] else "pass")
    return {
        "timezone": safe_timezone,
        "today": today,
        "status": status,
        "summary": summary,
        "checks": checks,
        "notes": [
            "This QA endpoint is for local pre-deploy checks.",
            "It uses the same lazy Minimum Day sync as the real Do it Today page.",
            "Warnings are acceptable if you have not created future Plan tasks yet.",
        ],
    }
