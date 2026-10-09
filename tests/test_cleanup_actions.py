
import pytest
from botocore.exceptions import ClientError

from cleanup_actions import (
    delete_ebs_volume,
    release_elastic_ip,
    terminate_ec2_instance,
)


class MockEC2Client:
    def __init__(self):
        self.calls = []

    def delete_volume(self, **kwargs):
        self.calls.append(("delete_volume", kwargs))
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def release_address(self, **kwargs):
        self.calls.append(("release_address", kwargs))
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def terminate_instances(self, **kwargs):
        self.calls.append(("terminate_instances", kwargs))
        return {"TerminatingInstances": []}


def test_delete_ebs_volume_calls_correct_api():
    client = MockEC2Client()

    result = delete_ebs_volume(
        "vol-test123",
        ec2_client=client,
    )

    assert client.calls == [
        ("delete_volume", {"VolumeId": "vol-test123"})
    ]
    assert result["resource_type"] == "ebs_volume"
    assert result["resource_id"] == "vol-test123"
    assert result["status"] == "requested"


def test_release_elastic_ip_calls_correct_api():
    client = MockEC2Client()

    result = release_elastic_ip(
        "eipalloc-test123",
        ec2_client=client,
    )

    assert client.calls == [
        (
            "release_address",
            {"AllocationId": "eipalloc-test123"},
        )
    ]
    assert result["resource_type"] == "elastic_ip"
    assert result["resource_id"] == "eipalloc-test123"
    assert result["status"] == "requested"


def test_terminate_ec2_instance_calls_correct_api():
    client = MockEC2Client()

    result = terminate_ec2_instance(
        "i-test123",
        ec2_client=client,
    )

    assert client.calls == [
        (
            "terminate_instances",
            {"InstanceIds": ["i-test123"]},
        )
    ]
    assert result["resource_type"] == "ec2_instance"
    assert result["resource_id"] == "i-test123"
    assert result["status"] == "requested"


@pytest.mark.parametrize(
    ("cleanup_function", "resource_id"),
    [
        (delete_ebs_volume, ""),
        (release_elastic_ip, ""),
        (terminate_ec2_instance, ""),
    ],
)
def test_cleanup_rejects_empty_resource_ids(
    cleanup_function,
    resource_id,
):
    client = MockEC2Client()

    with pytest.raises(ValueError):
        cleanup_function(
            resource_id,
            ec2_client=client,
        )

    assert client.calls == []


def test_ebs_deletion_errors_are_reported():
    class FailingEC2Client:
        def delete_volume(self, **kwargs):
            raise ClientError(
                {
                    "Error": {
                        "Code": "VolumeInUse",
                        "Message": "Volume is in use",
                    }
                },
                "DeleteVolume",
            )

    with pytest.raises(RuntimeError, match="Unable to delete EBS volume"):
        delete_ebs_volume(
            "vol-test123",
            ec2_client=FailingEC2Client(),
        )
