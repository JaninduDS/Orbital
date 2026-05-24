"""Pydantic models for the Orbital schedule."""
from __future__ import annotations

from datetime import datetime, time
from enum import Enum
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator

TZ = ZoneInfo("America/Toronto")

Weekday = Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_INDEX: dict[str, int] = {
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6,
}
WEEKDAY_ICAL: dict[str, str] = {
    "Mon": "MO", "Tue": "TU", "Wed": "WE", "Thu": "TH", "Fri": "FR", "Sat": "SA", "Sun": "SU",
}


class Priority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class TaskType(str, Enum):
    lecture = "lecture"
    reading = "reading"
    assignment = "assignment"
    presentation_prep = "presentation_prep"
    engagement = "engagement"
    lab = "lab"
    exam = "exam"
    other = "other"


class Lecture(BaseModel):
    day: Weekday
    start: time
    end: time
    location: str
    online_dates: list[str] = Field(default_factory=list)  # ISO date strings

    @field_validator("start", "end", mode="before")
    @classmethod
    def _parse_time(cls, v: object) -> object:
        if isinstance(v, str):
            return time.fromisoformat(v)
        return v


class Course(BaseModel):
    code: str
    name: str
    color: str  # hex like "#7C3AED"
    instructor: str
    lectures: list[Lecture] = Field(default_factory=list)
    textbook: str | None = None


class Task(BaseModel):
    id: str
    course: str | None = None  # course code, or None for non-course tasks
    title: str
    type: TaskType = TaskType.other
    due: datetime | None = None
    weight: int = Field(default=2, ge=1, le=4)
    priority: Priority = Priority.normal
    estimated_minutes: int = 30
    status: Literal["pending", "in_progress", "done"] = "pending"
    notes: str | None = None
    recurring: RecurringSpec | None = None

    @field_validator("due", mode="after")
    @classmethod
    def _ensure_tz(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=TZ)
        return v


class RecurringSpec(BaseModel):
    """Repeats this task weekly on the given day at the given time until `until`."""
    day: Weekday
    time: time
    until: datetime  # last occurrence (inclusive)
    start: datetime | None = None  # first occurrence (defaults to term.start)
    estimated_minutes: int | None = None  # override per-occurrence

    @field_validator("time", mode="before")
    @classmethod
    def _parse_time(cls, v: object) -> object:
        if isinstance(v, str):
            return time.fromisoformat(v)
        return v

    @field_validator("until", "start", mode="after")
    @classmethod
    def _ensure_tz(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=TZ)
        return v


Task.model_rebuild()


class Term(BaseModel):
    name: str
    start: datetime
    end: datetime
    off_days: list[str] = Field(default_factory=list)  # ISO dates

    @field_validator("start", "end", mode="after")
    @classmethod
    def _ensure_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=TZ)
        return v


class Schedule(BaseModel):
    term: Term
    courses: list[Course]
    tasks: list[Task] = Field(default_factory=list)

    def course_by_code(self, code: str) -> Course | None:
        return next((c for c in self.courses if c.code == code), None)


def load_schedule(path: Path) -> Schedule:
    import yaml
    raw = yaml.safe_load(path.read_text())
    return Schedule.model_validate(raw)


def dump_schedule(schedule: Schedule, path: Path) -> None:
    import yaml
    data = schedule.model_dump(mode="json", exclude_none=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
