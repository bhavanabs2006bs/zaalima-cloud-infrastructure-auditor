from __future__ import annotations

from typing import Any


def build_scan_results(
    ebs_findings: list[dict[str, Any]],
    eip_findings: list[dict[str, Any]],
    ec2_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Combine results from all cloud resource scanners
    into one consistent structure.
    """

    return {
        "ebs_volumes": ebs_findings,
        "elastic_ips": eip_findings,
        "ec2_instances": ec2_findings,
    }


def count_findings(
    scan_results: dict[str, Any],
) -> dict[str, int]:
    """
    Return the number of findings for each resource type.
    """

    return {
        "ebs_volumes": len(
            scan_results.get("ebs_volumes", [])
        ),
        "elastic_ips": len(
            scan_results.get("elastic_ips", [])
        ),
        "ec2_instances": len(
            scan_results.get("ec2_instances", [])
        ),
    }


if __name__ == "__main__":

    sample_results = build_scan_results(
        ebs_findings=[],
        eip_findings=[],
        ec2_findings=[],
    )

    print(sample_results)
    print(count_findings(sample_results))