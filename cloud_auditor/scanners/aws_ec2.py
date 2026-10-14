"""Scan for oversized/underutilized EC2 instances using CloudWatch CPU
utilization metrics averaged over a configurable lookback window.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cloud_auditor.scanners import Finding
from cloud_auditor.utils import estimate_ec2_monthly_cost, with_backoff

DEFAULT_LOOKBACK_DAYS = 14
DEFAULT_CPU_THRESHOLD_PCT = 5.0

# Suggests stepping down one size within the same family as a starting point.
# Not exhaustive — meant to give the operator a concrete next step, not the
# final word on rightsizing.
_DOWNSIZE_HINTS = {
    "xlarge": "large",
    "2xlarge": "xlarge",
    "4xlarge": "2xlarge",
    "large": "medium",
    "medium": "small",
}


def _suggest_downsize(instance_type: str) -> Optional[str]:
    if "." not in instance_type:
        return None
    family, size = instance_type.split(".", 1)
    smaller = _DOWNSIZE_HINTS.get(size)
    return f"{family}.{smaller}" if smaller else None


@with_backoff()
def _describe_running_instances(session, region: str):
    ec2 = session.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_instances")
    instances = []
    for page in paginator.paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    ):
        for reservation in page.get("Reservations", []):
            instances.extend(reservation.get("Instances", []))
    return instances


@with_backoff()
def _get_avg_cpu(session, region: str, instance_id: str, lookback_days: int) -> Optional[float]:
    cloudwatch = session.client("cloudwatch", region_name=region)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    resp = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=86400,  # daily datapoints
        Statistics=["Average"],
    )
    datapoints = resp.get("Datapoints", [])
    if not datapoints:
        return None
    return sum(dp["Average"] for dp in datapoints) / len(datapoints)


def scan_underutilized_ec2_instances(
    session,
    region: str,
    account_id: str,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    cpu_threshold_pct: float = DEFAULT_CPU_THRESHOLD_PCT,
) -> List[Finding]:
    findings: List[Finding] = []
    for inst in _describe_running_instances(session, region):
        instance_id = inst["InstanceId"]
        instance_type = inst.get("InstanceType", "unknown")

        avg_cpu = _get_avg_cpu(session, region, instance_id, lookback_days)
        if avg_cpu is None or avg_cpu >= cpu_threshold_pct:
            continue  # no data, or genuinely utilized — skip

        name_tag = next(
            (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), None
        )
        downsize_to = _suggest_downsize(instance_type)
        current_cost = estimate_ec2_monthly_cost(instance_type)
        new_cost = estimate_ec2_monthly_cost(downsize_to) if downsize_to else current_cost * 0.5

        findings.append(
            Finding(
                provider="aws",
                region=region,
                resource_type="ec2_instance",
                resource_id=instance_id,
                reason=(
                    f"Avg CPU {avg_cpu:.1f}% over {lookback_days}d is below "
                    f"{cpu_threshold_pct}% threshold ({instance_type})"
                    + (f", name='{name_tag}'" if name_tag else "")
                ),
                estimated_monthly_savings=round(max(current_cost - new_cost, 0), 2),
                cleanup_action=(
                    f"aws ec2 stop-instances --instance-ids {instance_id} --region {region}"
                    + (
                        f"  # then: aws ec2 modify-instance-attribute --instance-id {instance_id}"
                        f" --instance-type '{{\"Value\": \"{downsize_to}\"}}' --region {region}"
                        if downsize_to
                        else ""
                    )
                ),
                metadata={
                    "instance_type": instance_type,
                    "avg_cpu_pct": round(avg_cpu, 2),
                    "lookback_days": lookback_days,
                    "suggested_type": downsize_to,
                    "name_tag": name_tag,
                },
                severity="high" if avg_cpu < 1.0 else "medium",
                account_or_project=account_id,
            )
        )
    return findings
