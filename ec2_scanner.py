from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Any, Optional

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
)

from aws_client_factory import get_client


MAX_QUERIES_PER_REQUEST = 500
LOOKBACK_DAYS = 14
CPU_THRESHOLD = 5.0
METRIC_PERIOD_SECONDS = 86400
MIN_DAILY_DATAPOINTS = 14


def _safe_aws_error(exc: Exception) -> RuntimeError:
    """Return a safe error message without exposing arbitrary exception text."""
    if isinstance(exc, ClientError):
        error = exc.response.get("Error", {})
        detail = error.get("Code", "UnknownAWSCode")
    elif isinstance(exc, NoCredentialsError):
        detail = "AWS credentials are missing or unavailable"
    elif isinstance(exc, BotoCoreError):
        detail = f"AWS SDK error ({type(exc).__name__})"
    else:
        detail = f"unexpected error ({type(exc).__name__})"

    return RuntimeError(f"EC2 scanning failed: {detail}")


def find_ec2_instances(
    ec2_client=None,
    region_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return EC2 instance metadata using paginated AWS results."""
    ec2 = (
        ec2_client
        if ec2_client is not None
        else get_client("ec2", region_name=region_name)
    )
    findings = []

    try:
        paginator = ec2.get_paginator("describe_instances")

        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance.get("InstanceId")
                    if not instance_id:
                        continue

                    findings.append(
                        {
                            "resource_type": "ec2_instance",
                            "resource_id": instance_id,
                            "region": (
                                region_name
                                or ec2.meta.region_name
                            ),
                            "instance_type": instance.get("InstanceType"),
                            "state": instance.get("State", {}).get("Name"),
                            "launch_time": instance.get("LaunchTime"),
                        }
                    )

        return findings

    except Exception as exc:
        raise _safe_aws_error(exc) from exc


def _get_cpu_metric_summary(
    instance_ids: list[str],
    cloudwatch_client=None,
    region_name: Optional[str] = None,
) -> dict[str, dict[str, Optional[float] | int]]:
    """Return CPU averages and datapoint counts for the last 14 days."""
    if not instance_ids:
        return {}

    cloudwatch = (
        cloudwatch_client
        if cloudwatch_client is not None
        else get_client("cloudwatch", region_name=region_name)
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=LOOKBACK_DAYS)
    summaries: dict[str, dict[str, Optional[float] | int]] = {}

    try:
        for batch_start in range(
            0, len(instance_ids), MAX_QUERIES_PER_REQUEST
        ):
            batch_ids = instance_ids[
                batch_start:batch_start + MAX_QUERIES_PER_REQUEST
            ]

            queries = [
                {
                    "Id": f"cpu_{index}",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "CPUUtilization",
                            "Dimensions": [
                                {
                                    "Name": "InstanceId",
                                    "Value": instance_id,
                                }
                            ],
                        },
                        "Period": METRIC_PERIOD_SECONDS,
                        "Stat": "Average",
                    },
                    "ReturnData": True,
                }
                for index, instance_id in enumerate(
                    batch_ids, start=batch_start
                )
            ]

            values_by_query: dict[str, list[float]] = {}
            next_token = None

            while True:
                request = {
                    "MetricDataQueries": queries,
                    "StartTime": start_time,
                    "EndTime": end_time,
                    "ScanBy": "TimestampAscending",
                }

                if next_token:
                    request["NextToken"] = next_token

                response = cloudwatch.get_metric_data(**request)

                for result in response.get("MetricDataResults", []):
                    query_id = result.get("Id")
                    if not query_id:
                        continue

                    values_by_query.setdefault(query_id, []).extend(
                        result.get("Values", [])
                    )

                next_token = response.get("NextToken")
                if not next_token:
                    break

            for index, instance_id in enumerate(
                batch_ids, start=batch_start
            ):
                values = values_by_query.get(f"cpu_{index}", [])

                valid_values = [
                    float(value)
                    for value in values
                    if isinstance(value, (int, float))
                    and isfinite(value)
                    and 0 <= value <= 100
                ]

                average = (
                    sum(valid_values) / len(valid_values)
                    if valid_values
                    else None
                )

                summaries[instance_id] = {
                    "average": average,
                    "datapoint_count": len(valid_values),
                }

        return summaries

    except Exception as exc:
        raise _safe_aws_error(exc) from exc


def get_cpu_utilizations(
    instance_ids: list[str],
    cloudwatch_client=None,
    region_name: Optional[str] = None,
) -> dict[str, Optional[float]]:
    """Return average CPU utilization, or None when no valid data exists."""
    summaries = _get_cpu_metric_summary(
        instance_ids,
        cloudwatch_client=cloudwatch_client,
        region_name=region_name,
    )

    return {
        instance_id: summary["average"]
        for instance_id, summary in summaries.items()
    }


def find_underutilized_instances(
    ec2_client=None,
    cloudwatch_client=None,
    region_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Find running, sufficiently monitored instances averaging below 5% CPU."""
    instances = find_ec2_instances(
        ec2_client=ec2_client,
        region_name=region_name,
    )

    running_instances = [
        instance
        for instance in instances
        if instance.get("state") == "running"
    ]

    if not running_instances:
        return []

    # Exclude instances without a verifiable full 14-day history.
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    eligible_instances = []

    for instance in running_instances:
        launch_time = instance.get("launch_time")

        if not isinstance(launch_time, datetime):
            continue

        if launch_time.tzinfo is None:
            launch_time = launch_time.replace(tzinfo=timezone.utc)

        if launch_time <= cutoff:
            eligible_instances.append(instance)

    if not eligible_instances:
        return []

    summaries = _get_cpu_metric_summary(
        [instance["resource_id"] for instance in eligible_instances],
        cloudwatch_client=cloudwatch_client,
        region_name=region_name,
    )

    findings = []

    for instance in eligible_instances:
        instance_id = instance["resource_id"]
        summary = summaries.get(instance_id, {})
        cpu = summary.get("average")
        datapoint_count = summary.get("datapoint_count", 0)

        if datapoint_count < MIN_DAILY_DATAPOINTS:
            continue

        if cpu is None or cpu >= CPU_THRESHOLD:
            continue

        findings.append(
            {
                **instance,
                "average_cpu_14_days": round(cpu, 2),
                "cpu_datapoints_14_days": datapoint_count,
                "finding": "underutilized",
                "threshold": "<5%",
                "lookback_days": LOOKBACK_DAYS,
            }
        )

    return findings
