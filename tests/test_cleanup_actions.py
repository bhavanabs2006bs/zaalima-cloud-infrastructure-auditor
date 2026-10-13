import pytest
from botocore.exceptions import ClientError

from cleanup_actions import (
    delete_ebs_volume,
    release_elastic_ip,
    terminate_ec2_instance,
)


def test_elastic_ip_release_errors_include_aws_error_code():
    class FailingEC2Client:
        def release_address(self, **kwargs):
            raise ClientError(
                {"Error": {"Code": "DependencyViolation", "Message": "Address is associated"}},
                "ReleaseAddress",
            )

    with pytest.raises(RuntimeError, match="DependencyViolation"):
        release_elastic_ip("eipalloc-test123", ec2_client=FailingEC2Client())


def test_ec2_termination_errors_include_resource_id():
    class FailingEC2Client:
        def terminate_instances(self, **kwargs):
            raise ClientError(
                {"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "Instance not found"}},
                "TerminateInstances",
            )

    with pytest.raises(RuntimeError, match="i-test123"):
        terminate_ec2_instance("i-test123", ec2_client=FailingEC2Client())


def test_ebs_deletion_error_includes_aws_error_code():
    class FailingEC2Client:
        def delete_volume(self, **kwargs):
            raise ClientError(
                {"Error": {"Code": "VolumeInUse", "Message": "Volume is attached"}},
                "DeleteVolume",
            )

    with pytest.raises(RuntimeError, match="VolumeInUse"):
        delete_ebs_volume("vol-test123", ec2_client=FailingEC2Client())


def test_cleanup_rejects_empty_resource_ids():
    with pytest.raises(ValueError, match="must not be empty"):
        delete_ebs_volume("", ec2_client=object())

    with pytest.raises(ValueError, match="must not be empty"):
        release_elastic_ip("   ", ec2_client=object())

    with pytest.raises(ValueError, match="must not be empty"):
        terminate_ec2_instance("", ec2_client=object())


def test_ebs_delete_error_includes_resource_id():
    class FailingEC2Client:
        def delete_volume(self, **kwargs):
            raise ClientError(
                {"Error": {"Code": "VolumeInUse", "Message": "Volume is attached"}},
                "DeleteVolume",
            )

    with pytest.raises(RuntimeError, match="vol-test123"):
        delete_ebs_volume("vol-test123", ec2_client=FailingEC2Client())


def test_cleanup_does_not_expose_unexpected_exception_text():
    class FailingEC2Client:
        def delete_volume(self, **kwargs):
            raise RuntimeError("secret-token-value")

    with pytest.raises(RuntimeError) as exc_info:
        delete_ebs_volume("vol-test123", ec2_client=FailingEC2Client())

    assert "vol-test123" in str(exc_info.value)
    assert "secret-token-value" not in str(exc_info.value)
