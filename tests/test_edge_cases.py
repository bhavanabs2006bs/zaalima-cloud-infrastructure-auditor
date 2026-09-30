import boto3
from moto import mock_aws

from ebs_scanner import find_unattached_volumes
from eip_scanner import find_unassociated_elastic_ips


@mock_aws
def test_empty_account():
    """Verify scanners return empty results when no resources exist."""

    ec2 = boto3.client("ec2", region_name="us-east-1")

    ebs_results = find_unattached_volumes()
    eip_results = find_unassociated_elastic_ips(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert ebs_results == []
    assert eip_results == []


@mock_aws
def test_multi_region():
    """Verify scanners can work with different AWS regions."""

    regions = ["us-east-1", "us-west-2"]

    for region in regions:
        ec2 = boto3.client("ec2", region_name=region)

        findings = find_unassociated_elastic_ips(
            ec2_client=ec2,
            region_name=region,
        )

        assert findings == []