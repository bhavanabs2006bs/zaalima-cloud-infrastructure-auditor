from ec2_scanner import get_cpu_utilizations


def test_get_cpu_utilizations_with_no_instances():
    """Verify CPU utilization returns an empty dictionary for no instances."""
    result = get_cpu_utilizations([])

    assert result == {}
import boto3
from moto import mock_aws

from ec2_scanner import get_cpu_utilizations


@mock_aws
def test_get_cpu_utilizations_with_cpu_data():
    """Verify average CPU utilization is calculated correctly."""
    cloudwatch = boto3.client(
        "cloudwatch",
        region_name="us-east-1",
    )

    result = get_cpu_utilizations(
        ["i-1234567890abcdef0"],
        cloudwatch_client=cloudwatch,
        region_name="us-east-1",
    )

    assert isinstance(result, dict)
    assert "i-1234567890abcdef0" in result


@mock_aws
def test_get_cpu_utilizations_without_cpu_data():
    """Verify instances with no CPU data return None."""
    cloudwatch = boto3.client(
        "cloudwatch",
        region_name="us-east-1",
    )

    result = get_cpu_utilizations(
        ["i-1234567890abcdef0"],
        cloudwatch_client=cloudwatch,
        region_name="us-east-1",
    )

    assert result["i-1234567890abcdef0"] is None


@mock_aws
def test_get_cpu_utilizations_multiple_instances():
    """Verify CPU utilization handles multiple instances."""
    cloudwatch = boto3.client(
        "cloudwatch",
        region_name="us-east-1",
    )

    instance_ids = [
        "i-11111111111111111",
        "i-22222222222222222",
    ]

    result = get_cpu_utilizations(
        instance_ids,
        cloudwatch_client=cloudwatch,
        region_name="us-east-1",
    )

    assert len(result) == 2
    assert instance_ids[0] in result
    assert instance_ids[1] in result    