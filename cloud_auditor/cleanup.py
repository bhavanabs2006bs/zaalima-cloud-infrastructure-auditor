"""Safe resource cleanup: findings are always previewed in dry-run mode
first, and execution requires an explicit, per-run typed confirmation.
Nothing is ever deleted silently.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List

from rich.console import Console

console = Console()



def load_findings_from_report(path: str) -> List[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        findings = data.get("findings", [])
        if isinstance(findings, list):
            return findings

    raise ValueError(
        "Invalid report format: expected a list of findings "
        "or an object containing a 'findings' list."
    )


def print_dry_run(findings: List[dict]) -> None:
    if not findings:
        console.print("[green]Nothing to clean up.[/green]")
        return

    console.print(f"[bold]DRY RUN[/bold] — {len(findings)} action(s) would be taken. "
                   f"Nothing has been changed.\n")
    for f in findings:
        console.print(f"  [{f['provider'].upper()}] {f['resource_type']} {f['resource_id']}")
        console.print(f"    reason: {f['reason']}")
        console.print(f"    command: [cyan]{f['cleanup_action']}[/cyan]\n")


def execute_cleanup(findings: List[dict], confirm_token: str) -> None:
    """Run each finding's cleanup_action via the local AWS/gcloud CLI.

    Requires the caller to have already collected a typed confirmation
    (e.g. the user typing the exact string "DELETE") — this function does
    not prompt itself, keeping it safe to call from both the CLI's
    interactive prompt and from scripted/tested contexts.
    """
    if confirm_token != "DELETE":
        raise PermissionError(
            "Refusing to execute cleanup: confirmation token must be exactly 'DELETE'."
        )

    if not findings:
        console.print("[green]Nothing to clean up.[/green]")
        return

    console.print(f"[bold red]EXECUTING[/bold red] {len(findings)} cleanup action(s)...\n")
    successes, failures = 0, 0

    for f in findings:
        command = f["cleanup_action"].split("  #")[0].strip()  # drop inline comments/hints
        console.print(f"  → {command}")
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            console.print(f"    [green]done[/green] {result.stdout.strip()}")
            successes += 1
        except subprocess.CalledProcessError as exc:
            console.print(f"    [red]failed[/red]: {exc.stderr.strip()}")
            failures += 1

    console.print(f"\n[bold]{successes} succeeded, {failures} failed[/bold].")
