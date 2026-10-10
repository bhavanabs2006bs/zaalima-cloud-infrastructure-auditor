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
                {
                    "Error": {
                        "Code": "DependencyViolation",
                        "Message": "The address is still associated",
                    }
                },
                "ReleaseAddress",
            )

    with pytest.raises(RuntimeError, match="DependencyViolation"):
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

    with pytest.raises(RuntimeError, match="i-test123"):
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

    with pytest.raises(RuntimeError, match="VolumeInUse"):
        delete_ebs_volume(
            "vol-test123",
            ec2_client=FailingEC2Client(),
        )
