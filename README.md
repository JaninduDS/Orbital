# Orbital

A workload cockpit for a Waterloo physics student. Three pieces:

1. **Python data layer + CLI** (this directory) — single source of truth in `data/schedule.yaml`, exports to `.ics` and `state.json`.
2. **Quickshell QML widget** (`widget/`) — desktop panel that reads `state.json`. *(coming next)*
3. **iPhone bridge** — commits `calendar.ics` to a private GitHub repo; iOS subscribes via the raw URL.

## Setup (Arch + Hyprland, assumes nothing else)

```bash
# Install uv if you don't have it
sudo pacman -S uv git

# Clone / cd into this repo
cd ~/orbital

# Install Python deps
uv sync
```

## CLI quick tour

```bash
uv run orbital list           # today's lectures + tasks + slack
uv run orbital week           # next 7 days
uv run orbital add            # interactive: title, course, due, priority, ...
uv run orbital export ics     # → data/calendar.ics
uv run orbital export json    # → data/state.json (for the widget)
uv run orbital export all
uv run orbital sync --repo-dir ~/orbital-calendar   # iPhone sync, see below
```

`ORBITAL_HOME` overrides the project root if you call from elsewhere.

## Editing the schedule

`data/schedule.yaml` is the source of truth. Edit by hand or with `orbital add`.

- Each `task` may have either `due:` (one-off) or `recurring:` (weekly).
- `priority` is one of `low | normal | high | critical`; alarms scale accordingly.
- `term.off_days` cancels lectures and recurring tasks on those dates.
- `lectures[].online_dates` lists days that lecture is held online — flagged in the CLI and widget.

## iPhone calendar subscription

1. **Create a private repo** on GitHub (e.g. `orbital-calendar`). Empty is fine.
2. **Make a fine-grained PAT** with `Contents: Read and write` scope for that single repo, then clone over HTTPS or set up SSH.
   ```bash
   git clone git@github.com:USERNAME/orbital-calendar.git ~/orbital-calendar
   ```
3. **Push your `.ics`:**
   ```bash
   uv run orbital sync --repo-dir ~/orbital-calendar
   ```
   The command prints a raw URL like:
   `https://raw.githubusercontent.com/USERNAME/orbital-calendar/main/calendar.ics`
4. **On iPhone:**
   `Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar → paste raw URL.`
   Set refresh to **Every Hour**.

Alarm cadence per priority (configured in `orbital/export/ics.py`):

| Priority   | Alarms                |
|------------|-----------------------|
| critical   | 24h before + 1h before|
| high       | 2h before             |
| normal     | 30 min before         |
| low        | none                  |

## Quickshell widget

```bash
uv run orbital export json     # generate data/state.json
qs -p ~/orbital/widget         # opens the panel on the right edge
```

Auto-start with Hyprland — add to `~/.config/hypr/hyprland.conf`:
```
exec-once = qs -p ~/orbital/widget
bind = SUPER, O, exec, qs ipc call orbital toggle   # show/hide panel
```

Or call IPC directly:
```bash
qs ipc call orbital toggle   # toggle visibility
qs ipc call orbital show
qs ipc call orbital hide
```

The widget polls `data/state.json` every 60s and reacts to file changes immediately.

## Project layout

```
orbital/
├── data/schedule.yaml          # source of truth
├── orbital/
│   ├── core/{schema,loader,compute}.py
│   ├── export/{ics,widget_state}.py
│   ├── sync/git_push.py
│   └── cli.py
├── widget/                     # Quickshell QML (coming next)
├── scripts/orbital-daemon.sh   # dunst integration (coming next)
└── tests/
```
