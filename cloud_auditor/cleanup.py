
"""Safe cleanup helpers with dry-run, confirmation, and audit logging."""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from rich.console import Console

console = Console()

AUDIT_LOG_PATH = Path("logs") / "cleanup_audit.jsonl"


def load_findings_from_report(path: str) -> List[dict]:
    """Load findings from a JSON report."""
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
    """Display proposed cleanup actions without executing them."""
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


def _write_audit_log(
    finding: dict,
    status: str,
    command: str = "",
    error: str = "",
) -> None:
    """Append one JSON Lines audit event."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": finding.get("provider", "unknown"),
        "resource_type": finding.get("resource_type", "unknown"),
        "resource_id": finding.get("resource_id", "unknown"),
        "cleanup_action": finding.get("cleanup_action", ""),
        "command": command,
        "status": status,
        "error": error[:1000],
    }

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record) + "\n")


def _parse_cleanup_command(action: str) -> list[str]:
    """Validate and parse supported AWS CLI or gcloud commands."""
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Cleanup action must be a non-empty string.")

    if "\n" in action or "\r" in action:
        raise ValueError("Multi-line cleanup actions are not allowed.")

    # Remove an optional inline comment, preserving previous behavior.
    command_text = action.split("  #", 1)[0].strip()

    try:
        parts = shlex.split(command_text, posix=False)
    except ValueError as exc:
        raise ValueError(f"Invalid cleanup command: {exc}") from exc

    if not parts:
        raise ValueError("Cleanup action is empty.")

    executable = Path(parts[0].strip('"')).name.lower()

    allowed_executables = {
        "aws",
        "aws.exe",
        "gcloud",
        "gcloud.cmd",
        "gcloud.exe",
    }

    if executable not in allowed_executables:
        raise ValueError(
            "Unsupported cleanup command. Only AWS CLI and gcloud "
            "commands are permitted."
        )

    if any(
        operator in part
        for part in parts
        for operator in (";", "&&", "||", "|", ">", "<")
    ):
        raise ValueError("Shell operators are not allowed in cleanup actions.")

    return parts


def execute_cleanup(findings: List[dict], confirm_token: str) -> None:
    """Execute validated commands after confirmation and audit each attempt."""
    if confirm_token != "DELETE":
        for finding in findings:
            try:
                _write_audit_log(
                    finding,
                    status="rejected",
                    error="Confirmation token was not exactly DELETE.",
                )
            except OSError as exc:
                console.print(f"[red]Could not write audit log: {exc}[/red]")

        raise PermissionError(
            "Refusing to execute cleanup: confirmation token must be exactly "
            "'DELETE'."
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
            command = _parse_cleanup_command(
                finding.get("cleanup_action", "")
            )
        except (ValueError, OSError) as exc:
            try:
                _write_audit_log(
                    finding,
                    status="rejected",
                    error=str(exc),
                )
            except OSError as log_exc:
                console.print(
                    f"[red]Could not write audit log: {log_exc}[/red]"
                )

            console.print(f"  [red]rejected[/red]: {exc}")
            failures += 1
            continue

        command_text = " ".join(command)

        # Record the start before executing. If logging fails, skip execution.
        try:
            _write_audit_log(
                finding,
                status="started",
                command=command_text,
            )
        except OSError as exc:
            console.print(
                f"  [red]Audit log error; action skipped: {exc}[/red]"
            )
            failures += 1
            continue

        try:
            result = subprocess.run(
                command,
                shell=False,
                check=True,
                capture_output=True,
                text=True,
            )

            try:
                _write_audit_log(
                    finding,
                    status="success",
                    command=command_text,
                )
            except OSError as exc:
                console.print(
                    f"  [red]Could not record success: {exc}[/red]"
                )

            console.print(
                f"  [green]done[/green]: "
                f"{finding.get('resource_id', 'unknown')}"
            )
            successes += 1

        except (subprocess.CalledProcessError, OSError) as exc:
            error = getattr(exc, "stderr", None) or str(exc)

            try:
                _write_audit_log(
                    finding,
                    status="failed",
                    command=command_text,
                    error=error,
                )
            except OSError as log_exc:
                console.print(
                    f"  [red]Could not record failure: {log_exc}[/red]"
                )

            console.print(f"  [red]failed[/red]: {error}")
            failures += 1

    console.print(
        f"\nCleanup summary: {successes} succeeded, {failures} failed."
    )
