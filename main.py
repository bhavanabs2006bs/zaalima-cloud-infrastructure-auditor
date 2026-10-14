from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from ebs_scanner import find_unattached_volumes
from eip_scanner import find_unassociated_elastic_ips
from ec2_scanner import find_underutilized_instances
from scan_results import build_scan_results, count_findings

app = typer.Typer(
    name="cloud-auditor",
    help="Audit AWS resources for potential cost savings.",
)


@app.command()
def scan(
    region: str = typer.Option(
        "us-east-1",
        "--region",
        "-r",
        help="AWS region to scan.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional path for a JSON report.",
    ),
) -> None:
    """Scan for unattached EBS volumes, unassociated Elastic IPs,
    and underutilized EC2 instances.
    """
    try:
        ebs_findings = find_unattached_volumes(region_name=region)
        eip_findings = find_unassociated_elastic_ips(region_name=region)
        ec2_findings = find_underutilized_instances(region_name=region)

        results = build_scan_results(
            ebs_findings=ebs_findings,
            eip_findings=eip_findings,
            ec2_findings=ec2_findings,
        )

        report = {
            "region": region,
            "counts": count_findings(results),
            "findings": results,
        }
        report_json = json.dumps(report, indent=2, default=str)

        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(report_json + "\n", encoding="utf-8")
            typer.echo(f"Report saved to {output}")
        else:
            typer.echo(report_json)

    except Exception as exc:
        typer.echo(
            f"Scan failed: {type(exc).__name__}: {exc}",
            err=True,
        )
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
