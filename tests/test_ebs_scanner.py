from datetime import datetime, timezone

import boto3
from botocore.stub import Stubber

from ebs_scanner import find_unattached_volumes


def test_returns_only_unattached_volumes():

    client = boto3.client(
        "ec2",
        region_name="us-east-1",
    )

    stubber = Stubber(client)

    stubber.add_response(
        "describe_volumes",
        {
            "Volumes": [
                {
                    "VolumeId": "vol-free",
                    "Size": 50,
                    "VolumeType": "gp3",
                    "State": "available",
                    "Encrypted": True,
                    "AvailabilityZone": "us-east-1a",
                    "CreateTime": datetime(
                        2026,
                        9,
                        30,
                        tzinfo=timezone.utc,
                    ),
                    "Attachments": [],
                    "Tags": [],
                },
                {
                    "VolumeId": "vol-attached",
                    "Size": 100,
                    "VolumeType": "gp3",
                    "State": "in-use",
                    "Encrypted": True,
                    "AvailabilityZone": "us-east-1b",
                    "CreateTime": datetime(
                        2026,
                        9,
                        29,
                        tzinfo=timezone.utc,
                    ),
                    "Attachments": [
                        {
                            "InstanceId": "i-123"
                        }
                    ],
                    "Tags": [],
                },
            ]
        },
        {},
    )

    with stubber:

        findings = find_unattached_volumes(
            ec2_client=client
        )

    assert len(findings) == 1

    assert (
        findings[0]["resource_id"]
        == "vol-free"
    )

    assert (
        findings[0]["finding"]
        == "unattached"
    )

    assert (
        findings[0]["size_gb"]
        == 50
    )


def test_returns_empty_list_when_no_volumes_exist():

    client = boto3.client(
        "ec2",
        region_name="us-east-1",
    )

    stubber = Stubber(client)

    stubber.add_response(
        "describe_volumes",
        {
            "Volumes": []
        },
        {},
    )

    with stubber:

        findings = find_unattached_volumes(
            ec2_client=client
        )

    assert findings == []