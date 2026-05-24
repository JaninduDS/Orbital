"""Orbital command-line interface."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .core import loader
from .core.compute import (
    expand_lectures,
    expand_tasks,
    lectures_on,
    next_critical,
    occurrences_on,
    slack_minutes,
    upcoming,
)
from .core.schema import TZ, Priority, Task, TaskType
from .export.ics import write_ics
from .export.widget_state import write_state

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Orbital — physics workload cockpit.")
export_app = typer.Typer(no_args_is_help=True, help="Export schedule for downstream consumers.")
app.add_typer(export_app, name="export")

console = Console()


def _fmt_due(due: datetime, *, now: datetime | None = None) -> str:
    now = now or datetime.now(TZ)
    delta = due - now
    minutes = int(delta.total_seconds() // 60)
    if minutes < 0:
        return f"[red]overdue {(-minutes)//60}h[/red]"
    if minutes < 60:
        return f"in {minutes}m"
    if minutes < 60 * 24:
        return f"in {minutes // 60}h {minutes % 60}m"
    days = minutes // (60 * 24)
    return f"in {days}d ({due.strftime('%a %b %d %H:%M')})"


def _priority_style(p: Priority) -> str:
    return {
        Priority.critical: "bold red",
        Priority.high: "yellow",
        Priority.normal: "cyan",
        Priority.low: "dim",
    }[p]


@app.command()
def list() -> None:  # noqa: A001 — shadows builtin intentionally
    """Show today's lectures and tasks."""
    schedule = loader.load()
    occs = expand_tasks(schedule)
    lecs = expand_lectures(schedule)
    now = datetime.now(TZ)
    today = now.date()

    console.print(Panel.fit(f"[bold]Today — {today.strftime('%A %b %d, %Y')}[/bold]", border_style="blue"))

    lec_table = Table(title="Lectures", show_header=True, header_style="bold")
    lec_table.add_column("Time")
    lec_table.add_column("Course")
    lec_table.add_column("Room")
    for l in lectures_on(lecs, today):
        marker = " [yellow](online)[/yellow]" if l.is_online else ""
        lec_table.add_row(
            f"{l.start.strftime('%H:%M')}–{l.end.strftime('%H:%M')}",
            f"[{l.course.color}]{l.course.code}[/] {l.course.name}{marker}",
            l.lecture.location,
        )
    if lec_table.row_count == 0:
        console.print("[dim]No lectures today.[/dim]")
    else:
        console.print(lec_table)

    task_table = Table(title="Tasks due today / overdue", show_header=True, header_style="bold")
    task_table.add_column("Due")
    task_table.add_column("Pri")
    task_table.add_column("Course")
    task_table.add_column("Title")
    task_table.add_column("Est")
    todays_or_overdue = [o for o in occs if o.due.date() <= today and o.task.status != "done"]
    for o in sorted(todays_or_overdue, key=lambda o: o.due):
        task_table.add_row(
            _fmt_due(o.due, now=now),
            Text(o.priority.value, style=_priority_style(o.priority)),
            o.task.course or "-",
            o.task.title,
            f"{o.estimated_minutes}m",
        )
    if task_table.row_count == 0:
        console.print("[dim]Nothing due today.[/dim]")
    else:
        console.print(task_table)

    slack = slack_minutes(occs, lecs, now=now)
    label = f"slack: {slack//60}h {slack%60}m" if slack >= 0 else f"OVERBOOKED by {(-slack)//60}h {(-slack)%60}m"
    style = "green" if slack >= 0 else "bold red"
    console.print(Panel.fit(label, border_style=style))


@app.command()
def week() -> None:
    """Show the next 7 days."""
    schedule = loader.load()
    occs = expand_tasks(schedule)
    lecs = expand_lectures(schedule)
    now = datetime.now(TZ)
    today = now.date()

    crit = next_critical(occs, after=now)
    if crit:
        console.print(Panel.fit(
            f"Next critical: [bold]{crit.task.title}[/bold] — {_fmt_due(crit.due, now=now)}",
            border_style="red",
        ))

    for i in range(7):
        day = today + timedelta(days=i)
        day_lecs = lectures_on(lecs, day)
        day_tasks = occurrences_on(occs, day)
        if not day_lecs and not day_tasks:
            continue
        table = Table(title=day.strftime("%A %b %d"), show_header=True, header_style="bold")
        table.add_column("Time")
        table.add_column("Kind")
        table.add_column("Item")
        for l in day_lecs:
            table.add_row(
                l.start.strftime("%H:%M"),
                f"[{l.course.color}]lecture[/]",
                f"{l.course.code} @ {l.lecture.location}",
            )
        for o in sorted(day_tasks, key=lambda o: o.due):
            table.add_row(
                o.due.strftime("%H:%M"),
                Text(o.priority.value, style=_priority_style(o.priority)),
                f"[{o.task.course or '-'}] {o.task.title} ({o.estimated_minutes}m)",
            )
        console.print(table)


@app.command()
def add(
    title: Annotated[str, typer.Option(prompt=True, help="Task title")],
    course: Annotated[str, typer.Option(prompt=True, help="Course code, or '-' for none")] = "-",
    due: Annotated[str, typer.Option(prompt=True, help="Due (YYYY-MM-DD HH:MM or YYYY-MM-DDTHH:MM)")] = "",
    priority: Annotated[Priority, typer.Option(prompt=True)] = Priority.normal,
    estimated_minutes: Annotated[int, typer.Option(prompt=True)] = 30,
    type: Annotated[TaskType, typer.Option(prompt=True)] = TaskType.other,  # noqa: A002
    notes: Annotated[str, typer.Option(prompt=True)] = "",
) -> None:
    """Add a task to the schedule."""
    schedule = loader.load()
    due_dt: datetime | None = None
    if due.strip():
        s = due.strip().replace(" ", "T")
        due_dt = datetime.fromisoformat(s).replace(tzinfo=TZ)
    course_code: str | None = None if course.strip() in ("", "-") else course.strip().upper()
    if course_code and not schedule.course_by_code(course_code):
        console.print(f"[red]Unknown course: {course_code}[/red]")
        raise typer.Exit(1)
    task = Task(
        id=f"task-{uuid.uuid4().hex[:8]}",
        course=course_code,
        title=title,
        type=type,
        due=due_dt,
        priority=priority,
        estimated_minutes=estimated_minutes,
        notes=notes or None,
    )
    schedule.tasks.append(task)
    loader.save(schedule)
    console.print(f"[green]Added[/green] {task.id}: {title}")


@export_app.command("ics")
def export_ics() -> None:
    """Write the calendar to data/calendar.ics."""
    schedule = loader.load()
    path = write_ics(schedule, loader.ics_path())
    console.print(f"[green]Wrote[/green] {path}")


@export_app.command("json")
def export_json() -> None:
    """Write widget state to data/state.json."""
    schedule = loader.load()
    path = write_state(schedule, loader.state_path())
    console.print(f"[green]Wrote[/green] {path}")


@export_app.command("all")
def export_all() -> None:
    """Write both ics and json."""
    schedule = loader.load()
    write_ics(schedule, loader.ics_path())
    write_state(schedule, loader.state_path())
    console.print(f"[green]Wrote[/green] {loader.ics_path()} + {loader.state_path()}")


@app.command()
def sync(
    repo_dir: Annotated[str, typer.Option(help="Path to the git repo that hosts calendar.ics")] = "",
    push: Annotated[bool, typer.Option(help="Run git push after committing")] = True,
) -> None:
    """Re-export the .ics, commit it to a git repo, and (optionally) push."""
    from .sync.git_push import sync_calendar
    schedule = loader.load()
    write_ics(schedule, loader.ics_path())
    sync_calendar(loader.ics_path(), repo_dir=repo_dir or None, push=push, console=console)


if __name__ == "__main__":
    app()
