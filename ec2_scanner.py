from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
)

from aws_client_factory import get_client


def find_ec2_instances(
    ec2_client=None,
    region_name: Optional[str] = None,
) -> list[dict[str, Any]]:

    ec2 = ec2_client or get_client(
        "ec2",
        region_name=region_name,
    )

    findings = []

    try:
        paginator = ec2.get_paginator(
            "describe_instances"
        )

        for page in paginator.paginate():

            for reservation in page.get(
                "Reservations",
                [],
            ):

                for instance in reservation.get(
                    "Instances",
                    [],
                ):

                    instance_id = instance.get(
                        "InstanceId"
                    )

                    findings.append(
                        {
                            "resource_type": "ec2_instance",
                            "resource_id": instance_id,
                            "region": (
                                region_name
                                or ec2.meta.region_name
                            ),
                            "instance_type": instance.get(
                                "InstanceType"
                            ),
                            "state": instance.get(
                                "State", {}
                            ).get("Name"),
                            "launch_time": instance.get(
                                "LaunchTime"
                            ),
                        }
                    )

        return findings

    except (
        NoCredentialsError,
        BotoCoreError,
        ClientError,
    ) as exc:

        raise RuntimeError(
            f"Unable to scan EC2 instances: {exc}"
        ) from exc


def get_cpu_utilizations(
    instance_ids: list[str],
    cloudwatch_client=None,
    region_name: Optional[str] = None,
) -> dict[str, Optional[float]]:

    if not instance_ids:
        return {}

    cloudwatch = cloudwatch_client or get_client(
        "cloudwatch",
        region_name=region_name,
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=14)

    queries = []

    for index, instance_id in enumerate(instance_ids):

        queries.append(
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
                    "Period": 86400,
                    "Stat": "Average",
                },
                "ReturnData": True,
            }
        )

    try:
        response = cloudwatch.get_metric_data(
            MetricDataQueries=queries,
            StartTime=start_time,
            EndTime=end_time,
            ScanBy="TimestampDescending",
        )

        cpu_values = {}

        for index, instance_id in enumerate(instance_ids):

            result_id = f"cpu_{index}"

            result = next(
                (
                    item
                    for item in response.get(
                        "MetricDataResults",
                        [],
                    )
                    if item.get("Id") == result_id
                ),
                None,
            )

            if not result:
                cpu_values[instance_id] = None
                continue

            values = result.get("Values", [])

            if not values:
                cpu_values[instance_id] = None
                continue

            cpu_values[instance_id] = sum(values) / len(values)

        return cpu_values

    except (
        NoCredentialsError,
        BotoCoreError,
        ClientError,
    ) as exc:

        raise RuntimeError(
            f"Unable to read batch CPU metrics: {exc}"
        ) from exc


def find_underutilized_instances(
    ec2_client=None,
    cloudwatch_client=None,
    region_name: Optional[str] = None,
) -> list[dict[str, Any]]:

    instances = find_ec2_instances(
        ec2_client=ec2_client,
        region_name=region_name,
    )

    if not instances:
        return []

    instance_ids = [
        instance["resource_id"]
        for instance in instances
    ]

    cpu_values = get_cpu_utilizations(
        instance_ids,
        cloudwatch_client=cloudwatch_client,
        region_name=region_name,
    )

    findings = []

    for instance in instances:

        instance_id = instance["resource_id"]

        cpu = cpu_values.get(instance_id)

        # No CloudWatch data available
        if cpu is None:
            continue

        # Underutilized threshold
        if cpu < 5:

            finding = {
                **instance,
                "average_cpu_14_days": round(cpu, 2),
                "finding": "underutilized",
                "threshold": "<5%",
                "lookback_days": 14,
            }

            findings.append(finding)

    return findings