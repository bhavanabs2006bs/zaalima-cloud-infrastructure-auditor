from __future__ import annotations

from typing import Any, Optional

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
)

from aws_client_factory import get_client


def find_unassociated_elastic_ips(
    ec2_client=None,
    region_name: Optional[str] = None,
) -> list[dict[str, Any]]:

    ec2 = ec2_client or get_client(
        "ec2",
        region_name=region_name,
    )

    findings = []

    try:
        response = ec2.describe_addresses()

        for address in response.get(
            "Addresses",
            [],
        ):

            # Associated Elastic IP → not a finding
            if address.get("AssociationId"):
                continue

            finding = {
                "resource_type": "elastic_ip",
                "resource_id": (
                    address.get("AllocationId")
                    or address.get("PublicIp")
                ),
                "region": (
                    region_name
                    or ec2.meta.region_name
                ),
                "finding": "unassociated",
                "public_ip": address.get(
                    "PublicIp"
                ),
                "domain": address.get(
                    "Domain"
                ),
                "network_border_group": address.get(
                    "NetworkBorderGroup"
                ),
                "tags": address.get(
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
            f"Unable to scan Elastic IPs: {exc}"
        ) from exc


if __name__ == "__main__":

    results = find_unassociated_elastic_ips()

    for result in results:
        print(result)