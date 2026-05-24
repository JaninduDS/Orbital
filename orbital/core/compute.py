"""Workload calculations: expand recurring tasks, find slack, rank deadlines."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable

from .schema import (
    TZ,
    WEEKDAY_INDEX,
    Course,
    Lecture,
    Priority,
    Schedule,
    Task,
    TaskType,
)

PRIORITY_ORDER: dict[Priority, int] = {
    Priority.critical: 0,
    Priority.high: 1,
    Priority.normal: 2,
    Priority.low: 3,
}

# Working hours for the "slack" calculation.
WORK_DAY_START = time(8, 0)
WORK_DAY_END = time(23, 0)


@dataclass(frozen=True)
class Occurrence:
    """A concrete instance of a task at a specific datetime."""
    task: Task
    due: datetime
    estimated_minutes: int

    @property
    def course(self) -> str | None:
        return self.task.course

    @property
    def priority(self) -> Priority:
        return self.task.priority

    @property
    def title(self) -> str:
        return self.task.title


@dataclass(frozen=True)
class LectureOccurrence:
    course: Course
    lecture: Lecture
    start: datetime
    end: datetime
    is_online: bool

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() // 60)


def _now() -> datetime:
    return datetime.now(TZ)


def expand_tasks(schedule: Schedule, horizon_end: datetime | None = None) -> list[Occurrence]:
    """Expand one-off and recurring tasks into concrete occurrences."""
    end = horizon_end or schedule.term.end
    out: list[Occurrence] = []
    for task in schedule.tasks:
        if task.due is not None:
            out.append(Occurrence(task, task.due, task.estimated_minutes))
        if task.recurring is not None:
            r = task.recurring
            target_idx = WEEKDAY_INDEX[r.day]
            est = r.estimated_minutes or task.estimated_minutes
            # find first matching weekday on/after start (or term.start)
            origin = (r.start or schedule.term.start).date()
            delta = (target_idx - origin.weekday()) % 7
            cur_date = origin + timedelta(days=delta)
            until_date = min(r.until, end).date()
            while cur_date <= until_date:
                if cur_date.isoformat() not in schedule.term.off_days:
                    dt = datetime.combine(cur_date, r.time, tzinfo=TZ)
                    out.append(Occurrence(task, dt, est))
                cur_date += timedelta(days=7)
    out.sort(key=lambda o: o.due)
    return out


def expand_lectures(schedule: Schedule) -> list[LectureOccurrence]:
    out: list[LectureOccurrence] = []
    start_date = schedule.term.start.date()
    end_date = schedule.term.end.date()
    off = set(schedule.term.off_days)
    for course in schedule.courses:
        for lec in course.lectures:
            target_idx = WEEKDAY_INDEX[lec.day]
            cur = start_date + timedelta(days=(target_idx - start_date.weekday()) % 7)
            while cur <= end_date:
                if cur.isoformat() not in off:
                    s = datetime.combine(cur, lec.start, tzinfo=TZ)
                    e = datetime.combine(cur, lec.end, tzinfo=TZ)
                    out.append(LectureOccurrence(course, lec, s, e, cur.isoformat() in lec.online_dates))
                cur += timedelta(days=7)
    out.sort(key=lambda lo: lo.start)
    return out


def occurrences_on(occs: Iterable[Occurrence], day: date) -> list[Occurrence]:
    return [o for o in occs if o.due.date() == day]


def lectures_on(lecs: Iterable[LectureOccurrence], day: date) -> list[LectureOccurrence]:
    return [l for l in lecs if l.start.date() == day]


def upcoming(occs: Iterable[Occurrence], *, after: datetime | None = None, limit: int | None = None) -> list[Occurrence]:
    cutoff = after or _now()
    future = [o for o in occs if o.due >= cutoff and o.task.status != "done"]
    future.sort(key=lambda o: (PRIORITY_ORDER[o.priority], o.due))
    return future[:limit] if limit else future


def next_critical(occs: Iterable[Occurrence], *, after: datetime | None = None) -> Occurrence | None:
    cutoff = after or _now()
    crits = [o for o in occs if o.priority == Priority.critical and o.due >= cutoff and o.task.status != "done"]
    crits.sort(key=lambda o: o.due)
    return crits[0] if crits else None


def workload_minutes(occs: Iterable[Occurrence], day: date) -> int:
    return sum(o.estimated_minutes for o in occurrences_on(occs, day))


def lecture_minutes(lecs: Iterable[LectureOccurrence], day: date) -> int:
    return sum(l.duration_minutes for l in lectures_on(lecs, day))


def max_priority_on(occs: Iterable[Occurrence], day: date) -> Priority | None:
    todays = occurrences_on(occs, day)
    if not todays:
        return None
    return min((o.priority for o in todays), key=lambda p: PRIORITY_ORDER[p])


def remaining_minutes_today(now: datetime | None = None) -> int:
    now = now or _now()
    end = datetime.combine(now.date(), WORK_DAY_END, tzinfo=TZ)
    if now >= end:
        return 0
    start = datetime.combine(now.date(), WORK_DAY_START, tzinfo=TZ)
    effective = max(now, start)
    return int((end - effective).total_seconds() // 60)


def slack_minutes(
    occs: Iterable[Occurrence],
    lecs: Iterable[LectureOccurrence],
    now: datetime | None = None,
) -> int:
    now = now or _now()
    today = now.date()
    remaining = remaining_minutes_today(now)
    booked = workload_minutes(occs, today) + lecture_minutes(lecs, today)
    return remaining - booked


def heatmap(
    occs: Iterable[Occurrence],
    *,
    start: date,
    weeks: int = 8,
) -> list[list[dict[str, object]]]:
    """Return weeks x 7 grid. Each cell: {date, minutes, max_priority, count}."""
    occs = list(occs)
    grid: list[list[dict[str, object]]] = []
    for w in range(weeks):
        row: list[dict[str, object]] = []
        for d in range(7):
            day = start + timedelta(days=w * 7 + d)
            todays = occurrences_on(occs, day)
            mp = min((o.priority for o in todays), key=lambda p: PRIORITY_ORDER[p]) if todays else None
            row.append({
                "date": day.isoformat(),
                "minutes": sum(o.estimated_minutes for o in todays),
                "max_priority": mp.value if mp else None,
                "count": len(todays),
            })
        grid.append(row)
    return grid
