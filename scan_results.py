from __future__ import annotations

from typing import Any


SCAN_RESULT_KEYS = (
    "ebs_volumes",
    "elastic_ips",
    "ec2_instances",
)


def _validate_findings(
    findings: list[dict[str, Any]],
    name: str,
) -> None:
    if not isinstance(findings, list):
        raise TypeError(f"{name} must be a list")

    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise TypeError(
                f"{name}[{index}] must be a dictionary"
            )


def build_scan_results(
    ebs_findings: list[dict[str, Any]],
    eip_findings: list[dict[str, Any]],
    ec2_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Combine findings from all resource scanners."""

    _validate_findings(ebs_findings, "ebs_findings")
    _validate_findings(eip_findings, "eip_findings")
    _validate_findings(ec2_findings, "ec2_findings")

    return {
        "ebs_volumes": ebs_findings,
        "elastic_ips": eip_findings,
        "ec2_instances": ec2_findings,
    }


def count_findings(
    scan_results: dict[str, Any],
) -> dict[str, int]:
    """Count findings by resource category."""

    if not isinstance(scan_results, dict):
        raise TypeError("scan_results must be a dictionary")

    counts: dict[str, int] = {}

    for key in SCAN_RESULT_KEYS:
        findings = scan_results.get(key, [])

        if not isinstance(findings, list):
            raise TypeError(f"{key} must be a list")

        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                raise TypeError(
                    f"{key}[{index}] must be a dictionary"
                )

        counts[key] = len(findings)

    return counts


if __name__ == "__main__":
    sample_results = build_scan_results(
        ebs_findings=[],
        eip_findings=[],
        ec2_findings=[],
    )

    print(sample_results)
    print(count_findings(sample_results))
