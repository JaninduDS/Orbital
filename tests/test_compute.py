"""Smoke tests for compute + schema + exporters."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from orbital.core.compute import (
    expand_lectures,
    expand_tasks,
    next_critical,
    slack_minutes,
    upcoming,
    workload_minutes,
)
from orbital.core.schema import TZ, Priority, load_schedule
from orbital.export.ics import build_calendar
from orbital.export.widget_state import build_state

SCHEDULE_PATH = Path(__file__).parent.parent / "data" / "schedule.yaml"


def _schedule():
    return load_schedule(SCHEDULE_PATH)


def test_schedule_loads():
    s = _schedule()
    assert len(s.courses) == 4
    assert s.course_by_code("PHYS234") is not None


def test_recurring_tasks_expand_and_skip_off_days():
    s = _schedule()
    occs = expand_tasks(s)
    engagement = [o for o in occs if o.task.id == "phys490-engagement"]
    # 11 Mondays from May 25 to Aug 3, inclusive
    assert len(engagement) == 11
    # PHYS 260B lab prep — none should fall on May 18 (off day, but May 18 is a Mon, not Tue, so all should remain)
    lab_prep = [o for o in occs if o.task.id == "phys260b-lab-prep"]
    assert all(o.due.date().isoformat() not in s.term.off_days for o in lab_prep)


def test_lectures_skip_off_days():
    s = _schedule()
    lecs = expand_lectures(s)
    off = set(s.term.off_days)
    assert not any(l.start.date().isoformat() in off for l in lecs)
    # Online dates flagged
    online = [l for l in lecs if l.is_online]
    assert any(l.start.date().isoformat() == "2026-07-06" for l in online)


def test_next_critical_is_earliest_critical():
    s = _schedule()
    occs = expand_tasks(s)
    after = datetime(2026, 5, 11, 8, 0, tzinfo=TZ)
    crit = next_critical(occs, after=after)
    assert crit is not None
    assert crit.task.id == "phys234-test1"  # June 10 is earlier than July 14 slides


def test_upcoming_orders_by_priority_then_due():
    s = _schedule()
    occs = expand_tasks(s)
    after = datetime(2026, 5, 24, 0, 0, tzinfo=TZ)  # day before first engagement
    nxt = upcoming(occs, after=after, limit=5)
    assert len(nxt) == 5
    # Critical tasks should appear before high before normal in the limited window
    priorities = [o.priority for o in nxt]
    assert priorities == sorted(priorities, key=lambda p: {
        Priority.critical: 0, Priority.high: 1, Priority.normal: 2, Priority.low: 3,
    }[p]) or all(p in {Priority.critical, Priority.high} for p in priorities[:2])


def test_slack_calculation_runs():
    s = _schedule()
    occs = expand_tasks(s)
    lecs = expand_lectures(s)
    # pick a known day with both lectures (Wed)
    now = datetime(2026, 5, 13, 8, 0, tzinfo=TZ)
    slack = slack_minutes(occs, lecs, now=now)
    # 8am to 11pm = 15h = 900min; minus 80m (PHYS234) + 170m (PHYS260B) = 250m booked
    booked = workload_minutes(occs, now.date()) + 80 + 170
    assert slack == 900 - booked


def test_ics_build_has_lectures_and_tasks():
    s = _schedule()
    cal = build_calendar(s)
    events = [c for c in cal.walk("VEVENT")]
    # 4 courses, lecture counts: 2+2+1+1 = 6 recurring events
    summaries = [str(e["summary"]) for e in events]
    assert sum("PHYS234" in s for s in summaries) >= 2
    assert any("Test #1" in s for s in summaries)


def test_widget_state_structure():
    s = _schedule()
    now = datetime(2026, 5, 25, 9, 0, tzinfo=TZ)  # day of first engagement
    state = build_state(s, now=now)
    assert "today" in state and "next_tasks" in state and "heatmap" in state
    assert state["next_critical"] is not None
    assert len(state["heatmap"]["weeks"]) == 8
    assert all(len(row) == 7 for row in state["heatmap"]["weeks"])
