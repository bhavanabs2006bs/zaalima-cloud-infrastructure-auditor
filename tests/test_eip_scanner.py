import boto3
from botocore.stub import Stubber

from eip_scanner import (
    find_unassociated_elastic_ips,
)


def test_returns_only_unassociated_ips():

    client = boto3.client(
        "ec2",
        region_name="us-east-1",
    )

    stubber = Stubber(client)

    stubber.add_response(
        "describe_addresses",
        {
            "Addresses": [
                {
                    "AllocationId": "eipalloc-free",
                    "PublicIp": "203.0.113.10",
                    "Domain": "vpc",
                    "Tags": [],
                },
                {
                    "AllocationId": "eipalloc-used",
                    "PublicIp": "203.0.113.11",
                    "Domain": "vpc",
                    "AssociationId": "eipassoc-123",
                    "Tags": [],
                },
            ]
        },
        {},
    )

    with stubber:

        findings = find_unassociated_elastic_ips(
            ec2_client=client
        )

    assert len(findings) == 1

    assert (
        findings[0]["resource_id"]
        == "eipalloc-free"
    )

    assert (
        findings[0]["finding"]
        == "unassociated"
    )


def test_returns_empty_list_when_no_elastic_ips_exist():

    client = boto3.client(
        "ec2",
        region_name="us-east-1",
    )

    stubber = Stubber(client)

    stubber.add_response(
        "describe_addresses",
        {
            "Addresses": []
        },
        {},
    )

    with stubber:

        findings = find_unassociated_elastic_ips(
            ec2_client=client
        )

    assert findings == []