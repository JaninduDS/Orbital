"""Export the schedule as an iCalendar (.ics) file for iPhone subscription."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from icalendar import Alarm, Calendar, Event, vRecur

from ..core.compute import expand_lectures, expand_tasks
from ..core.schema import (
    TZ,
    WEEKDAY_ICAL,
    Priority,
    Schedule,
    Task,
)

ALARM_OFFSETS: dict[Priority, list[timedelta]] = {
    Priority.critical: [timedelta(hours=-24), timedelta(hours=-1)],
    Priority.high: [timedelta(hours=-2)],
    Priority.normal: [timedelta(minutes=-30)],
    Priority.low: [],
}

PRODID = "-//Orbital//Physics Workload Cockpit//EN"


def _uid(*parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]
    return f"{h}@orbital"


def _alarms_for(priority: Priority, summary: str) -> list[Alarm]:
    alarms: list[Alarm] = []
    for offset in ALARM_OFFSETS[priority]:
        a = Alarm()
        a.add("action", "DISPLAY")
        a.add("trigger", offset)
        a.add("description", summary)
        alarms.append(a)
    return alarms


def _add_lecture_events(cal: Calendar, schedule: Schedule) -> None:
    off_dates = {
        datetime.fromisoformat(d).replace(tzinfo=TZ) for d in schedule.term.off_days
    }
    for course in schedule.courses:
        for lec in course.lectures:
            # find the first occurrence on/after term.start matching lec.day
            from ..core.schema import WEEKDAY_INDEX
            start_date = schedule.term.start.date()
            target = WEEKDAY_INDEX[lec.day]
            first = start_date + timedelta(days=(target - start_date.weekday()) % 7)
            dtstart = datetime.combine(first, lec.start, tzinfo=TZ)
            dtend = datetime.combine(first, lec.end, tzinfo=TZ)

            ev = Event()
            ev.add("uid", _uid("lecture", course.code, lec.day, lec.start.isoformat()))
            ev.add("summary", f"{course.code} — {course.name}")
            online_note = ""
            if lec.online_dates:
                online_note = f"\nOnline on: {', '.join(lec.online_dates)}"
            ev.add(
                "description",
                f"{course.instructor}{online_note}",
            )
            ev.add("location", lec.location)
            ev.add("dtstart", dtstart)
            ev.add("dtend", dtend)
            ev.add(
                "rrule",
                vRecur(
                    freq="WEEKLY",
                    byday=WEEKDAY_ICAL[lec.day],
                    until=schedule.term.end,
                ),
            )
            # EXDATE for off-days that land on this weekday
            ex = []
            for od in off_dates:
                if od.weekday() == target:
                    ex.append(datetime.combine(od.date(), lec.start, tzinfo=TZ))
            if ex:
                ev.add("exdate", ex)
            cal.add_component(ev)


def _add_task_events(cal: Calendar, schedule: Schedule) -> None:
    occs = expand_tasks(schedule)
    for occ in occs:
        task: Task = occ.task
        ev = Event()
        ev.add(
            "uid",
            _uid("task", task.id, occ.due.isoformat()),
        )
        title = task.title
        if task.course:
            title = f"[{task.course}] {title}"
        ev.add("summary", title)
        if task.notes:
            ev.add("description", task.notes)
        ev.add("dtstart", occ.due)
        ev.add("dtend", occ.due + timedelta(minutes=max(15, occ.estimated_minutes)))
        for alarm in _alarms_for(task.priority, title):
            ev.add_component(alarm)
        cal.add_component(ev)


def build_calendar(schedule: Schedule) -> Calendar:
    cal = Calendar()
    cal.add("prodid", PRODID)
    cal.add("version", "2.0")
    cal.add("x-wr-calname", f"Orbital — {schedule.term.name}")
    cal.add("x-wr-timezone", "America/Toronto")
    _add_lecture_events(cal, schedule)
    _add_task_events(cal, schedule)
    return cal


def write_ics(schedule: Schedule, path: Path) -> Path:
    cal = build_calendar(schedule)
    path.write_bytes(cal.to_ical())
    return path
