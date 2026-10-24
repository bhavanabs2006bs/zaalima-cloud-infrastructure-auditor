
"""Safely validate and execute cleanup commands with audit logging."""

import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console


console = Console()

AUDIT_LOG_PATH = Path("logs") / "cleanup_audit.jsonl"

ALLOWED_EXECUTABLES = {
    "aws",
    "aws.exe",
    "gcloud",
    "gcloud.cmd",
    "gcloud.exe",
}

SHELL_OPERATORS = (";", "&&", "||", "|", ">", "<")


def load_findings_from_report(path: str) -> list[dict[str, Any]]:
    """Load findings from a JSON report file.

    Supports a JSON list or an object containing a 'findings' list.
    """
    report_path = Path(path)

    try:
        with report_path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON report: {exc}") from exc

    if isinstance(data, list):
        findings = data
    elif isinstance(data, dict):
        findings = data.get("findings")
        if not isinstance(findings, list):
            raise ValueError("Report must contain a 'findings' list.")
    else:
        raise ValueError(
            "Report must be a list or an object containing findings."
        )

    if not all(isinstance(item, dict) for item in findings):
        raise ValueError("Every finding must be a JSON object.")

    return findings


def print_dry_run(findings: list[dict[str, Any]]) -> None:
    """Display proposed cleanup actions without executing them."""
    console.print("\n[bold cyan]Cleanup Dry Run[/bold cyan]")
    console.print("No cloud resources will be changed.\n")

    if not findings:
        console.print("[yellow]No findings to process.[/yellow]")
        return

    for index, finding in enumerate(findings, start=1):
        console.print(f"{index}. Provider: {finding.get('provider', 'unknown')}")
        console.print(
            f"   Resource type: {finding.get('resource_type', 'unknown')}"
        )
        console.print(
            f"   Resource ID: {finding.get('resource_id', 'unknown')}"
        )
        console.print(
            f"   Proposed action: "
            f"{finding.get('cleanup_action', 'No action specified')}"
        )


def _write_audit_log(
    finding: dict[str, Any],
    status: str,
    command: str = "",
    error: str = "",
) -> None:
    """Append a cleanup event to the JSON Lines audit log."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": finding.get("provider", "unknown"),
        "resource_type": finding.get("resource_type", "unknown"),
        "resource_id": finding.get("resource_id", "unknown"),
        "cleanup_action": finding.get("cleanup_action", ""),
        "command": command,
        "status": status,
        "error": error,
    }

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _parse_cleanup_command(action: str) -> list[str]:
    """Validate and split an approved cloud CLI command.

    Commands are executed without a shell. This validation does not
    guarantee that a cloud operation is safe or non-destructive.
    """
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Cleanup command must be a non-empty string.")

    if "\n" in action or "\r" in action:
        raise ValueError("Multiline cleanup commands are not allowed.")

    # Remove an inline comment introduced by two or more spaces.
    action = action.split("  #", maxsplit=1)[0].strip()

    if not action:
        raise ValueError("Cleanup command is empty after removing comments.")

    try:
        parts = shlex.split(action, posix=False)
    except ValueError as exc:
        raise ValueError(f"Invalid cleanup command: {exc}") from exc

    if not parts:
        raise ValueError("Cleanup command cannot be empty.")

    executable = Path(parts[0].strip('"')).name.lower()

    if executable not in ALLOWED_EXECUTABLES:
        raise ValueError(
            "Unsupported cleanup command: only approved AWS CLI "
            "or Google Cloud CLI commands are allowed."
        )

    if any(
        operator in argument
        for argument in parts
        for operator in SHELL_OPERATORS
    ):
        raise ValueError("Shell operators are not allowed.")

    return parts


def execute_cleanup(
    findings: list[dict[str, Any]],
    confirm_token: str,
) -> None:
    """Execute validated cleanup commands after explicit confirmation.

    Requires the exact confirmation token 'DELETE'. Actions are logged
    before execution and again after success or failure.
    """
    if confirm_token != "DELETE":
        console.print(
            "[red]Cleanup cancelled: confirmation token must be DELETE.[/red]"
        )

        # Retain resource details when a finding is available.
        audit_finding = (
            findings[0]
            if (
                isinstance(findings, list)
                and findings
                and isinstance(findings[0], dict)
            )
            else {}
        )

        try:
            _write_audit_log(
                audit_finding,
                status="rejected",
                error="Confirmation token missing or incorrect.",
            )
        except OSError as exc:
            console.print(f"[red]Could not write audit log: {exc}[/red]")

        raise PermissionError(
            "Cleanup requires the exact confirmation token 'DELETE'."
        )

    if not isinstance(findings, list):
        raise ValueError("Findings must be provided as a list.")

    if not findings:
        console.print("[yellow]No findings to clean up.[/yellow]")
        return

    console.print("\n[bold cyan]Executing Cleanup[/bold cyan]")
    console.print(
        "[yellow]Confirmation accepted. Review each action carefully.[/yellow]"
    )

    successes = 0
    failures = 0

    for finding in findings:
        if not isinstance(finding, dict):
            console.print(
                "[red]rejected[/red]: Finding must be an object."
            )
            failures += 1
            continue

        resource_id = finding.get("resource_id")

        if (
            not isinstance(resource_id, (str, int))
            or isinstance(resource_id, bool)
            or not str(resource_id).strip()
        ):
            try:
                _write_audit_log(
                    finding,
                    status="rejected",
                    error="Missing or invalid resource_id.",
                )
            except OSError as log_exc:
                console.print(
                    f"[red]Could not write audit log: {log_exc}[/red]"
                )

            console.print(
                "  [red]rejected[/red]: Missing or invalid resource_id."
            )
            failures += 1
            continue

        try:
            command = _parse_cleanup_command(
                finding.get("cleanup_action", "")
            )
        except (ValueError, TypeError) as exc:
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

        command_text = subprocess.list2cmdline(command)

        # Do not execute a command if the start event cannot be recorded.
        try:
            _write_audit_log(
                finding,
                status="started",
                command=command_text,
            )
        except OSError as exc:
            console.print(
                f"[red]Skipping command: could not write start audit log: "
                f"{exc}[/red]"
            )
            failures += 1
            continue

        try:
            subprocess.run(
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
                    f"[red]WARNING: command completed, but the success "
                    f"audit entry could not be written: {exc}[/red]"
                )

            console.print(f"  [green]success[/green]: {resource_id}")
            successes += 1

        except (subprocess.CalledProcessError, OSError) as exc:
            if isinstance(exc, subprocess.CalledProcessError):
                error_message = (
                    str(exc.stderr).strip()
                    if exc.stderr
                    else str(exc)
                )
            else:
                error_message = str(exc)

            try:
                _write_audit_log(
                    finding,
                    status="failed",
                    command=command_text,
                    error=error_message,
                )
            except OSError as log_exc:
                console.print(
                    f"[red]Could not write failure audit log: "
                    f"{log_exc}[/red]"
                )

            console.print(
                f"  [red]failed[/red]: {resource_id} — {error_message}"
            )
            failures += 1

    console.print("\n[bold]Cleanup Summary[/bold]")
    console.print(f"Successful actions: {successes}")
    console.print(f"Failed or rejected actions: {failures}")
