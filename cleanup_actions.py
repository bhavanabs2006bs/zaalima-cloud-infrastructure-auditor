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


def _handle_cleanup_error(
    operation: str,
    resource_id: str,
    exc: Exception,
) -> RuntimeError:
    """Create a safe cleanup error without exposing unexpected details."""
    if isinstance(exc, ClientError):
        error = exc.response.get("Error", {})
        error_code = error.get("Code", "UnknownAWSCode")
        detail = f"AWS error ({error_code})"
    elif isinstance(exc, NoCredentialsError):
        detail = "AWS credentials are missing or unavailable"
    elif isinstance(exc, BotoCoreError):
        detail = f"AWS SDK error ({type(exc).__name__})"
    else:
        detail = f"unexpected error ({type(exc).__name__})"

    return RuntimeError(
        f"Unable to {operation} resource {resource_id}: {detail}"
    )


def delete_ebs_volume(
    volume_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
    *,
    confirm: bool = False,
) -> dict:
    """Delete an EBS volume only after explicit confirmation."""
    if not volume_id or not volume_id.strip():
        raise ValueError("volume_id must not be empty")

    if confirm is not True:
        raise ValueError(
            "Explicit confirmation is required for destructive cleanup"
        )

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
    except Exception as exc:
        raise _handle_cleanup_error(
            "delete EBS volume",
            volume_id,
            exc,
        ) from exc


def release_elastic_ip(
    allocation_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
    *,
    confirm: bool = False,
) -> dict:
    """Release an Elastic IP only after explicit confirmation."""
    if not allocation_id or not allocation_id.strip():
        raise ValueError("allocation_id must not be empty")

    if confirm is not True:
        raise ValueError(
            "Explicit confirmation is required for destructive cleanup"
        )

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
    except Exception as exc:
        raise _handle_cleanup_error(
            "release Elastic IP",
            allocation_id,
            exc,
        ) from exc


def terminate_ec2_instance(
    instance_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
    *,
    confirm: bool = False,
) -> dict:
    """Terminate an EC2 instance only after explicit confirmation."""
    if not instance_id or not instance_id.strip():
        raise ValueError("instance_id must not be empty")

    if confirm is not True:
        raise ValueError(
            "Explicit confirmation is required for destructive cleanup"
        )

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
    except Exception as exc:
        raise _handle_cleanup_error(
            "terminate EC2 instance",
            instance_id,
            exc,
        ) from exc
