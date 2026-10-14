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

_SEVERITY_STYLE = {"high": "bold red", "medium": "yellow", "low": "dim"}


def render_findings_table(findings: List[Finding], title: str = "Audit Findings") -> None:
    if not findings:
        console.print("[green]✓ No wasteful or misconfigured resources found.[/green]")
        return

    table = Table(title=title, show_lines=False, header_style="bold cyan")
    table.add_column("Provider")
    table.add_column("Region/Zone")
    table.add_column("Type")
    table.add_column("Resource ID", overflow="fold")
    table.add_column("Reason", overflow="fold")
    table.add_column("Est. $/mo", justify="right")
    table.add_column("Severity")

    total_savings = 0.0
    for f in sorted(findings, key=lambda x: x.estimated_monthly_savings, reverse=True):
        style = _SEVERITY_STYLE.get(f.severity, "white")
        table.add_row(
            f.provider.upper(),
            f.region,
            f.resource_type,
            f.resource_id,
            f.reason,
            f"${f.estimated_monthly_savings:,.2f}",
            Text(f.severity, style=style),
        )
        total_savings += f.estimated_monthly_savings

    console.print(table)
    console.print(
        f"\n[bold]{len(findings)} finding(s)[/bold] — "
        f"estimated total savings: [bold green]${total_savings:,.2f}/month[/bold green]"
    )


def _findings_to_dicts(findings: List[Finding]) -> List[dict]:
    return [asdict(f) for f in findings]


def export_json(findings: List[Finding], path: str) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finding_count": len(findings),
        "estimated_total_monthly_savings": round(
            sum(f.estimated_monthly_savings for f in findings), 2
        ),
        "findings": _findings_to_dicts(findings),
    }
    out_path = Path(path)
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    return str(out_path)


def export_csv(findings: List[Finding], path: str) -> str:
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
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for f in findings:
            row = asdict(f)
            row["metadata"] = json.dumps(row["metadata"], default=str)
            writer.writerow(row)
    return str(out_path)


def export(findings: List[Finding], path: str) -> str:
    """Dispatch to the right exporter based on file extension."""
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        return export_json(findings, path)
    if suffix == ".csv":
        return export_csv(findings, path)
    raise ValueError(f"Unsupported export format '{suffix}'. Use .json or .csv.")
