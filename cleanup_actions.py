
from __future__ import annotations

from typing import Optional

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
)

from aws_client_factory import get_client


def _get_ec2_client(
    ec2_client=None,
    region_name: Optional[str] = None,
):
    """Reuse an injected client or create an AWS EC2 client."""
    return ec2_client or get_client(
        "ec2",
        region_name=region_name,
    )


def delete_ebs_volume(
    volume_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
) -> dict:
    """Delete a specified EBS volume."""
    if not volume_id or not volume_id.strip():
        raise ValueError("volume_id must not be empty")

    ec2 = _get_ec2_client(ec2_client, region_name)

    try:
        response = ec2.delete_volume(VolumeId=volume_id)

        return {
            "resource_type": "ebs_volume",
            "resource_id": volume_id,
            "action": "delete",
            "status": "requested",
            "response": response,
        }

    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Unable to delete EBS volume {volume_id}: {exc}"
        ) from exc


def release_elastic_ip(
    allocation_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
) -> dict:
    """Release a specified Elastic IP allocation."""
    if not allocation_id or not allocation_id.strip():
        raise ValueError("allocation_id must not be empty")

    ec2 = _get_ec2_client(ec2_client, region_name)

    try:
        response = ec2.release_address(
            AllocationId=allocation_id
        )

        return {
            "resource_type": "elastic_ip",
            "resource_id": allocation_id,
            "action": "release",
            "status": "requested",
            "response": response,
        }

    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Unable to release Elastic IP {allocation_id}: {exc}"
        ) from exc


def terminate_ec2_instance(
    instance_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
) -> dict:
    """Request termination of a specified EC2 instance."""
    if not instance_id or not instance_id.strip():
        raise ValueError("instance_id must not be empty")

    ec2 = _get_ec2_client(ec2_client, region_name)

    try:
        response = ec2.terminate_instances(
            InstanceIds=[instance_id]
        )

        return {
            "resource_type": "ec2_instance",
            "resource_id": instance_id,
            "action": "terminate",
            "status": "requested",
            "response": response,
        }

    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Unable to terminate EC2 instance {instance_id}: {exc}"
        ) from exc
