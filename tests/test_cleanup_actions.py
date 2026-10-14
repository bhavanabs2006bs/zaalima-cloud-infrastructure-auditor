import pytest
from botocore.exceptions import ClientError

from cleanup_actions import (
    delete_ebs_volume,
    release_elastic_ip,
    terminate_ec2_instance,
)


class FakeEC2:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def _call(self, operation, **kwargs):
        self.calls.append((operation, kwargs))
        if self.error:
            raise self.error
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def delete_volume(self, **kwargs):
        return self._call("delete_volume", **kwargs)

    def release_address(self, **kwargs):
        return self._call("release_address", **kwargs)

    def terminate_instances(self, **kwargs):
        return self._call("terminate_instances", **kwargs)


def make_client_error(
    code="InvalidRequest",
    message="AWS rejected request",
):
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "CleanupOperation",
    )


def test_ebs_delete_calls_correct_aws_operation():
    ec2 = FakeEC2()

    result = delete_ebs_volume(
        "vol-123",
        ec2_client=ec2,
        confirm=True,
    )

    assert ec2.calls == [
        ("delete_volume", {"VolumeId": "vol-123"})
    ]
    assert result["resource_id"] == "vol-123"
    assert result["status"] == "requested"


def test_elastic_ip_release_calls_correct_aws_operation():
    ec2 = FakeEC2()

    result = release_elastic_ip(
        "eipalloc-123",
        ec2_client=ec2,
        confirm=True,
    )

    assert ec2.calls == [
        ("release_address", {"AllocationId": "eipalloc-123"})
    ]
    assert result["resource_id"] == "eipalloc-123"
    assert result["status"] == "requested"


def test_ec2_termination_calls_correct_aws_operation():
    ec2 = FakeEC2()

    result = terminate_ec2_instance(
        "i-123",
        ec2_client=ec2,
        confirm=True,
    )

    assert ec2.calls == [
        ("terminate_instances", {"InstanceIds": ["i-123"]})
    ]
    assert result["resource_id"] == "i-123"
    assert result["status"] == "requested"


@pytest.mark.parametrize(
    ("operation", "resource_id"),
    [
        (delete_ebs_volume, ""),
        (delete_ebs_volume, "   "),
        (release_elastic_ip, ""),
        (release_elastic_ip, "   "),
        (terminate_ec2_instance, ""),
        (terminate_ec2_instance, "   "),
    ],
)
def test_cleanup_rejects_empty_resource_ids(operation, resource_id):
    ec2 = FakeEC2()

    with pytest.raises(ValueError):
        operation(
            resource_id,
            ec2_client=ec2,
            confirm=True,
        )

    assert ec2.calls == []


@pytest.mark.parametrize(
    ("operation", "resource_id", "expected_code"),
    [
        (delete_ebs_volume, "vol-123", "VolumeInUse"),
        (
            release_elastic_ip,
            "eipalloc-123",
            "InvalidAllocationID.NotFound",
        ),
        (
            terminate_ec2_instance,
            "i-123",
            "InvalidInstanceID.NotFound",
        ),
    ],
)
def test_cleanup_errors_include_resource_and_aws_error_code(
    operation,
    resource_id,
    expected_code,
):
    ec2 = FakeEC2(
        error=make_client_error(code=expected_code)
    )

    with pytest.raises(RuntimeError) as exc_info:
        operation(
            resource_id,
            ec2_client=ec2,
            confirm=True,
        )

    assert resource_id in str(exc_info.value)
    assert expected_code in str(exc_info.value)


def test_cleanup_does_not_expose_unexpected_exception_text():
    ec2 = FakeEC2(
        error=RuntimeError("secret-token-value")
    )

    with pytest.raises(RuntimeError) as exc_info:
        delete_ebs_volume(
            "vol-123",
            ec2_client=ec2,
            confirm=True,
        )

    assert "vol-123" in str(exc_info.value)
    assert "secret-token-value" not in str(exc_info.value)
    assert "RuntimeError" in str(exc_info.value)


@pytest.mark.parametrize(
    ("operation", "resource_id"),
    [
        (delete_ebs_volume, "vol-123"),
        (release_elastic_ip, "eipalloc-123"),
        (terminate_ec2_instance, "i-123"),
    ],
)
def test_cleanup_requires_explicit_confirmation(
    operation,
    resource_id,
):
    ec2 = FakeEC2()

    with pytest.raises(
        ValueError,
        match="Explicit confirmation",
    ):
        operation(
            resource_id,
            ec2_client=ec2,
        )

    assert ec2.calls == []
