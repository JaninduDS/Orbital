"""Commit and push calendar.ics to a private git repo for iPhone subscription."""
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _remote_raw_url(repo_dir: Path, branch: str, filename: str) -> str | None:
    try:
        url = _run(["git", "remote", "get-url", "origin"], repo_dir).stdout.strip()
    except subprocess.CalledProcessError:
        return None
    # normalize git@github.com:user/repo.git -> https://raw.githubusercontent.com/user/repo/<branch>/file
    if url.startswith("git@github.com:"):
        user_repo = url.removeprefix("git@github.com:").removesuffix(".git")
    elif url.startswith("https://github.com/"):
        user_repo = url.removeprefix("https://github.com/").removesuffix(".git")
    else:
        return None
    return f"https://raw.githubusercontent.com/{user_repo}/{branch}/{filename}"


def sync_calendar(
    ics_path: Path,
    *,
    repo_dir: Path | str | None,
    push: bool = True,
    console: Console | None = None,
) -> None:
    """Copy `ics_path` into a git repo, commit it, and push.

    If `repo_dir` is None, prints setup instructions and exits.
    """
    console = console or Console()
    if not repo_dir:
        console.print(
            "[yellow]No --repo-dir given.[/yellow] To enable iPhone sync:\n"
            "  1. Create a private GitHub repo (e.g. `orbital-calendar`).\n"
            "  2. Clone it locally:  git clone git@github.com:USER/orbital-calendar.git\n"
            "  3. Run:  orbital sync --repo-dir ~/orbital-calendar\n"
            "  4. On iPhone: Settings → Calendar → Accounts → Add Account → Other →\n"
            "     Add Subscribed Calendar → paste the raw URL it prints.\n"
        )
        return

    repo = Path(repo_dir).expanduser().resolve()
    if not (repo / ".git").exists():
        console.print(f"[red]{repo} is not a git repository.[/red]")
        return

    dest = repo / "calendar.ics"
    shutil.copyfile(ics_path, dest)

    try:
        _run(["git", "add", "calendar.ics"], repo)
        # only commit if there are staged changes
        status = _run(["git", "status", "--porcelain"], repo).stdout
        if status.strip():
            msg = f"Update calendar.ics — {datetime.now().isoformat(timespec='seconds')}"
            _run(["git", "commit", "-m", msg], repo)
            console.print(f"[green]Committed:[/green] {msg}")
        else:
            console.print("[dim]No changes to commit.[/dim]")
            return

        if push:
            _run(["git", "push"], repo)
            console.print("[green]Pushed to origin.[/green]")
            branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()
            raw = _remote_raw_url(repo, branch, "calendar.ics")
            if raw:
                console.print(f"\n[bold]Subscribe on iPhone:[/bold] {raw}")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]git failed:[/red] {e.stderr or e.stdout}")
