import boto3
from moto import mock_aws

from ec2_scanner import find_ec2_instances


@mock_aws
def test_find_ec2_instances_returns_instance_details():
    """Verify EC2 scanner returns the expected instance details."""

    ec2 = boto3.client("ec2", region_name="us-east-1")

    response = ec2.run_instances(
        ImageId="ami-12345678",
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",
    )

    instance_id = response["Instances"][0]["InstanceId"]

    findings = find_ec2_instances(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert len(findings) == 1
    assert findings[0]["resource_type"] == "ec2_instance"
    assert findings[0]["resource_id"] == instance_id
    assert findings[0]["instance_type"] == "t2.micro"
    assert findings[0]["state"] == "running"
    assert findings[0]["region"] == "us-east-1"


@mock_aws
def test_find_ec2_instances_empty_account():
    """Verify EC2 scanner returns an empty list when no instances exist."""

    ec2 = boto3.client("ec2", region_name="us-east-1")

    findings = find_ec2_instances(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert findings == []