"""Locate and load the Orbital schedule."""
from __future__ import annotations

import os
from pathlib import Path

from .schema import Schedule, dump_schedule, load_schedule


def project_root() -> Path:
    env = os.environ.get("ORBITAL_HOME")
    if env:
        return Path(env).expanduser().resolve()
    # walk up from cwd looking for data/schedule.yaml
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / "data" / "schedule.yaml").exists():
            return p
    # fall back to ~/orbital
    return Path.home() / "orbital"


def schedule_path() -> Path:
    return project_root() / "data" / "schedule.yaml"


def state_path() -> Path:
    return project_root() / "data" / "state.json"


def ics_path() -> Path:
    return project_root() / "data" / "calendar.ics"


def load() -> Schedule:
    return load_schedule(schedule_path())


def save(schedule: Schedule) -> None:
    dump_schedule(schedule, schedule_path())
