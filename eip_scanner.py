from __future__ import annotations

from typing import Any, Optional

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
)

from aws_client_factory import get_client


def _safe_error(exc: Exception) -> RuntimeError:
    if isinstance(exc, ClientError):
        error_code = exc.response.get("Error", {}).get(
            "Code", "UnknownAWSCode"
        )
        message = f"AWS error ({error_code})"
    elif isinstance(exc, NoCredentialsError):
        message = "AWS credentials are missing or unavailable"
    elif isinstance(exc, BotoCoreError):
        message = f"AWS SDK error ({type(exc).__name__})"
    else:
        message = f"unexpected error ({type(exc).__name__})"

    return RuntimeError(
        f"Unable to scan Elastic IPs: {message}"
    )


def find_unassociated_elastic_ips(
    ec2_client=None,
    region_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    ec2 = ec2_client or get_client(
        "ec2",
        region_name=region_name,
    )

    findings: list[dict[str, Any]] = []

    try:
        # describe_addresses is not a boto3 paginator operation.
        # Call it directly; AWS returns the available addresses in one response.
        response = ec2.describe_addresses()

        for address in response.get("Addresses", []):
            if address.get("AssociationId"):
                continue

            resource_id = (
                address.get("AllocationId")
                or address.get("PublicIp")
            )

            if not resource_id:
                continue

            findings.append({
                "resource_type": "elastic_ip",
                "resource_id": resource_id,
                "region": region_name or ec2.meta.region_name,
                "finding": "unassociated",
                "public_ip": address.get("PublicIp"),
                "domain": address.get("Domain"),
                "network_border_group": address.get(
                    "NetworkBorderGroup"
                ),
                "tags": address.get("Tags", []),
            })

        return findings

    except Exception as exc:
        raise _safe_error(exc) from exc


if __name__ == "__main__":
    for result in find_unassociated_elastic_ips():
        print(result)
