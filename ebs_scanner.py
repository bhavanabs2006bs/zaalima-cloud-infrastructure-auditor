from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
)

from aws_client_factory import get_client


def _iso(value: Any) -> Optional[str]:
    if isinstance(value, datetime):
        return value.isoformat()

    return value


def find_unattached_volumes(
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
            "describe_volumes"
        )

        for page in paginator.paginate():

            for volume in page.get("Volumes", []):

                # Attached volumes are not findings
                if volume.get("Attachments"):
                    continue

                finding = {
                    "resource_type": "ebs_volume",
                    "resource_id": volume["VolumeId"],
                    "region": (
                        region_name
                        or ec2.meta.region_name
                    ),
                    "finding": "unattached",
                    "state": volume.get("State"),
                    "size_gb": volume.get("Size"),
                    "volume_type": volume.get("VolumeType"),
                    "encrypted": volume.get(
                        "Encrypted",
                        False,
                    ),
                    "availability_zone": volume.get(
                        "AvailabilityZone"
                    ),
                    "created_at": _iso(
                        volume.get("CreateTime")
                    ),
                    "tags": volume.get(
                        "Tags",
                        [],
                    ),
                }

                findings.append(finding)

        return findings

    except (
        NoCredentialsError,
        BotoCoreError,
        ClientError,
    ) as exc:

        raise RuntimeError(
            f"Unable to scan EBS volumes: {exc}"
        ) from exc


if __name__ == "__main__":

    results = find_unattached_volumes()

    for result in results:
        print(result)