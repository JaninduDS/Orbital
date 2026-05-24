"""Build the state.json blob the Quickshell widget polls."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from ..core.compute import (
    expand_lectures,
    expand_tasks,
    heatmap,
    lectures_on,
    next_critical,
    slack_minutes,
    upcoming,
)
from ..core.schema import TZ, Schedule


def _course_lookup(schedule: Schedule) -> dict[str, dict[str, str]]:
    return {
        c.code: {"name": c.name, "color": c.color, "instructor": c.instructor}
        for c in schedule.courses
    }


def build_state(schedule: Schedule, now: datetime | None = None) -> dict:
    now = now or datetime.now(TZ)
    today = now.date()
    courses = _course_lookup(schedule)
    occs = expand_tasks(schedule)
    lecs = expand_lectures(schedule)

    today_lectures = [
        {
            "course": l.course.code,
            "title": l.course.name,
            "color": l.course.color,
            "start": l.start.isoformat(),
            "end": l.end.isoformat(),
            "location": l.lecture.location,
            "online": l.is_online,
        }
        for l in lectures_on(lecs, today)
    ]

    next_tasks = upcoming(occs, after=now, limit=3)
    next_tasks_payload = [
        {
            "id": o.task.id,
            "title": o.task.title,
            "course": o.task.course,
            "color": courses.get(o.task.course or "", {}).get("color", "#94A3B8"),
            "due": o.due.isoformat(),
            "due_in_minutes": int((o.due - now).total_seconds() // 60),
            "estimated_minutes": o.estimated_minutes,
            "priority": o.priority.value,
            "type": o.task.type.value,
            "status": o.task.status,
        }
        for o in next_tasks
    ]

    crit = next_critical(occs, after=now)
    next_critical_payload = None
    if crit:
        next_critical_payload = {
            "title": crit.task.title,
            "course": crit.task.course,
            "due": crit.due.isoformat(),
            "due_in_minutes": int((crit.due - now).total_seconds() // 60),
        }

    # 8-week heatmap starting on the Monday of the current week
    start_monday = today - timedelta(days=today.weekday())
    grid = heatmap(occs, start=start_monday, weeks=8)

    slack = slack_minutes(occs, lecs, now=now)

    return {
        "generated_at": now.isoformat(),
        "term": {
            "name": schedule.term.name,
            "start": schedule.term.start.date().isoformat(),
            "end": schedule.term.end.date().isoformat(),
        },
        "courses": courses,
        "today": {
            "date": today.isoformat(),
            "lectures": today_lectures,
            "slack_minutes": slack,
        },
        "next_tasks": next_tasks_payload,
        "next_critical": next_critical_payload,
        "heatmap": {
            "start": start_monday.isoformat(),
            "weeks": grid,
        },
    }


def write_state(schedule: Schedule, path: Path, now: datetime | None = None) -> Path:
    payload = build_state(schedule, now=now)
    path.write_text(json.dumps(payload, indent=2))
    return path
