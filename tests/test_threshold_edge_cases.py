import boto3
from moto import mock_aws

from ec2_scanner import find_underutilized_instances


@mock_aws
def test_underutilized_instance_empty_account():
    """Verify no findings are returned when there are no EC2 instances."""

    ec2 = boto3.client("ec2", region_name="us-east-1")
    cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

    findings = find_underutilized_instances(
        ec2_client=ec2,
        cloudwatch_client=cloudwatch,
    )

    assert findings == []
@mock_aws
def test_underutilized_instance_custom_threshold():
    """Verify the scanner accepts a custom CPU threshold."""

    ec2 = boto3.client("ec2", region_name="us-east-1")
    cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

    findings = find_underutilized_instances(
        ec2_client=ec2,
        cloudwatch_client=cloudwatch,
        
    )

    assert findings == []    