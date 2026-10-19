
"""Render scan findings as a Rich terminal table, and export them to
CSV/JSON for management review.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table
from rich.text import Text

from cloud_auditor.scanners import Finding

console = Console()

_SEVERITY_STYLE = {
    "high": "bold red",
    "medium": "yellow",
    "low": "dim",
}

_SEVERITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}


def render_findings_table(
    findings: List[Finding],
    title: str = "Audit Findings",
    sort_by: str = "savings",
) -> None:
    """Display findings in a Rich table, sorted by savings or severity."""

    if not findings:
        console.print(
            "[green] No wasteful or misconfigured resources found.[/green]"
        )
        return

    if sort_by not in {"savings", "severity"}:
        raise ValueError("sort_by must be 'savings' or 'severity'.")

    table = Table(
        title=title,
        show_lines=False,
        header_style="bold cyan",
    )

    table.add_column("Provider")
    table.add_column("Region/Zone")
    table.add_column("Type")
    table.add_column("Resource ID", overflow="fold")
    table.add_column("Reason", overflow="fold")
    table.add_column("Est. $/mo", justify="right")
    table.add_column("Severity")

    if sort_by == "severity":
        sorted_findings = sorted(
            findings,
            key=lambda finding: _SEVERITY_ORDER.get(
                finding.severity.lower(), 3
            ),
        )
    else:
        sorted_findings = sorted(
            findings,
            key=lambda finding: finding.estimated_monthly_savings,
            reverse=True,
        )

    total_savings = 0.0

    for finding in sorted_findings:
        severity = finding.severity.lower()
        style = _SEVERITY_STYLE.get(severity, "white")

        table.add_row(
            finding.provider.upper(),
            finding.region,
            finding.resource_type,
            finding.resource_id,
            finding.reason,
            f"${finding.estimated_monthly_savings:,.2f}",
            Text(finding.severity, style=style),
        )

        total_savings += finding.estimated_monthly_savings

    console.print(table)
    console.print(
        f"\n[bold]{len(findings)} finding(s)[/bold] - "
        f"estimated total savings: "
        f"[bold green]${total_savings:,.2f}/month[/bold green]"
    )


def _findings_to_dicts(findings: List[Finding]) -> List[dict]:
    """Convert Finding objects into dictionaries."""
    return [asdict(finding) for finding in findings]


def export_json(findings: List[Finding], path: str) -> str:
    """Export findings and summary information to a JSON file."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finding_count": len(findings),
        "estimated_total_monthly_savings": round(
            sum(finding.estimated_monthly_savings for finding in findings),
            2,
        ),
        "findings": _findings_to_dicts(findings),
    }

    out_path = Path(path)
    out_path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )

    return str(out_path)


def export_csv(findings: List[Finding], path: str) -> str:
    """Export findings to a CSV file."""
    out_path = Path(path)

    fieldnames = [
        "provider",
        "region",
        "resource_type",
        "resource_id",
        "reason",
        "estimated_monthly_savings",
        "severity",
        "account_or_project",
        "cleanup_action",
        "metadata",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for finding in findings:
            row = asdict(finding)
            row["metadata"] = json.dumps(row["metadata"], default=str)
            writer.writerow(row)

    return str(out_path)


def export(findings: List[Finding], path: str) -> str:
    """Choose the exporter based on the output file extension."""
    suffix = Path(path).suffix.lower()

    if suffix == ".json":
        return export_json(findings, path)

    if suffix == ".csv":
        return export_csv(findings, path)

    raise ValueError(
        f"Unsupported export format '{suffix}'. Use .json or .csv."
    )
