
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
    """Create a consistent, actionable cleanup error."""
    if isinstance(exc, ClientError):
        error = exc.response.get("Error", {})
        error_code = error.get("Code", "UnknownAWSCode")
        error_message = error.get(
            "Message",
            "AWS rejected the request",
        )
        detail = f"{error_code}: {error_message}"
    elif isinstance(exc, NoCredentialsError):
        detail = "AWS credentials are missing or unavailable"
    else:
        detail = str(exc) or "AWS request failed"

    return RuntimeError(
        f"Unable to {operation} resource {resource_id}: {detail}"
    )


def delete_ebs_volume(
    volume_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
) -> dict:
    """Request deletion of a specified EBS volume."""
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
        raise _handle_cleanup_error(
            "delete EBS volume",
            volume_id,
            exc,
        ) from exc


def release_elastic_ip(
    allocation_id: str,
    ec2_client=None,
    region_name: Optional[str] = None,
) -> dict:
    """Request release of a specified Elastic IP allocation."""
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
        raise _handle_cleanup_error(
            "release Elastic IP",
            allocation_id,
            exc,
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
        raise _handle_cleanup_error(
            "terminate EC2 instance",
            instance_id,
            exc,
        ) from exc
    
def test_elastic_ip_release_errors_include_aws_error_code():
    class FailingEC2Client:
        def release_address(self, **kwargs):
            raise ClientError(
                {
                    "Error": {
                        "Code": "DependencyViolation",
                        "Message": "The address is still associated",
                    }
                },
                "ReleaseAddress",
            )

    with pytest.raises(
        RuntimeError,
        match="DependencyViolation",
    ):
        release_elastic_ip(
            "eipalloc-test123",
            ec2_client=FailingEC2Client(),
        )


def test_ec2_termination_errors_include_resource_id():
    class FailingEC2Client:
        def terminate_instances(self, **kwargs):
            raise ClientError(
                {
                    "Error": {
                        "Code": "InvalidInstanceID.NotFound",
                        "Message": "The instance does not exist",
                    }
                },
                "TerminateInstances",
            )

    with pytest.raises(
        RuntimeError,
        match="i-test123",
    ):
        terminate_ec2_instance(
            "i-test123",
            ec2_client=FailingEC2Client(),
        )


def test_ebs_deletion_error_includes_aws_error_code():
    class FailingEC2Client:
        def delete_volume(self, **kwargs):
            raise ClientError(
                {
                    "Error": {
                        "Code": "VolumeInUse",
                        "Message": "The volume is currently attached",
                    }
                },
                "DeleteVolume",
            )

    with pytest.raises(
        RuntimeError,
        match="VolumeInUse",
    ):
        delete_ebs_volume(
            "vol-test123",
            ec2_client=FailingEC2Client(),
        )

