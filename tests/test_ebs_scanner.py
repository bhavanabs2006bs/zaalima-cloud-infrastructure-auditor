import boto3
from moto import mock_aws

from ebs_scanner import find_unattached_volumes


@mock_aws
def test_find_unattached_volume():
    """Verify that an unattached EBS volume is detected."""

    ec2 = boto3.client("ec2", region_name="us-east-1")

    volume = ec2.create_volume(
        AvailabilityZone="us-east-1a",
        Size=8,
    )

    volume_id = volume["VolumeId"]

    unattached_volumes = find_unattached_volumes()

    assert volume_id in unattached_volumes


@mock_aws
def test_no_unattached_volumes():
    """Verify empty result when no EBS volumes exist."""

    boto3.client("ec2", region_name="us-east-1")

    unattached_volumes = find_unattached_volumes()

    assert unattached_volumes == []