
"""Safe cleanup helpers with dry-run and explicit confirmation."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import List

from rich.console import Console

console = Console()


def load_findings_from_report(path: str) -> List[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))

    if isinstance(data, list):
        findings = data
    elif isinstance(data, dict) and isinstance(data.get("findings"), list):
        findings = data["findings"]
    else:
        raise ValueError(
            "Invalid report format: expected a list of findings "
            "or an object containing a 'findings' list."
        )

    if not all(isinstance(item, dict) for item in findings):
        raise ValueError("Invalid report: each finding must be an object.")

    return findings


def print_dry_run(findings: List[dict]) -> None:
    if not findings:
        console.print("[green]Nothing to clean up.[/green]")
        return

    console.print(
        f"[bold]DRY RUN[/bold] - {len(findings)} action(s) would be taken. "
        "Nothing has been changed.\n"
    )

    for finding in findings:
        console.print(
            f"  [{str(finding.get('provider', 'unknown')).upper()}] "
            f"{finding.get('resource_type', 'unknown')} "
            f"{finding.get('resource_id', 'unknown')}"
        )
        console.print(f"    reason: {finding.get('reason', 'Not provided')}")
        console.print(
            f"    action: {finding.get('cleanup_action', 'Not provided')}\n"
        )


def _parse_cleanup_command(action: str) -> list[str]:
    """Validate and parse supported cloud CLI cleanup commands."""
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Cleanup action must be a non-empty string.")

    if "\n" in action or "\r" in action:
        raise ValueError("Multi-line cleanup actions are not allowed.")

    # Allow comments/hints following the command, matching the old behavior.
    command_text = action.split("  #", 1)[0].strip()

    try:
        parts = shlex.split(command_text, posix=False)
    except ValueError as exc:
        raise ValueError(f"Invalid cleanup command: {exc}") from exc

    if not parts:
        raise ValueError("Cleanup action is empty.")

    executable = Path(parts[0].strip('"')).name.lower()

    # Only explicitly supported cloud CLI executables are allowed.
    if executable not in {"aws", "aws.exe", "gcloud", "gcloud.cmd", "gcloud.exe"}:
        raise ValueError(
            "Unsupported cleanup command. Only AWS CLI and gcloud commands "
            "are permitted."
        )

    if any(part in {";", "&&", "||", "|", ">", "<"} for part in parts):
        raise ValueError("Shell operators are not allowed in cleanup actions.")

    return parts


def execute_cleanup(findings: List[dict], confirm_token: str) -> None:
    """Execute validated cleanup actions after explicit confirmation."""
    if confirm_token != "DELETE":
        raise PermissionError(
            "Refusing to execute cleanup: confirmation token must be exactly 'DELETE'."
        )

    if not findings:
        console.print("[green]Nothing to clean up.[/green]")
        return

    console.print(
        f"[bold red]EXECUTING[/bold red] {len(findings)} cleanup action(s)...\n"
    )

    successes = 0
    failures = 0

    for finding in findings:
        try:
            command = _parse_cleanup_command(finding.get("cleanup_action", ""))
            console.print(f"  Running: {' '.join(command)}")

            result = subprocess.run(
                command,
                shell=False,
                check=True,
                capture_output=True,
                text=True,
            )

            console.print(f"    [green]done[/green] {result.stdout.strip()}")
            successes += 1

        except (ValueError, subprocess.CalledProcessError, OSError) as exc:
            console.print(f"    [red]failed[/red]: {exc}")
            failures += 1

    console.print(
        f"\nCleanup summary: {successes} succeeded, {failures} failed."
    )
