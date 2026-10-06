import boto3
from moto import mock_aws

from ebs_scanner import find_unattached_volumes
from eip_scanner import find_unassociated_elastic_ips


@mock_aws
def test_ebs_result_schema():
    """Validate the schema of EBS scanner results."""
    ec2 = boto3.client("ec2", region_name="us-east-1")

    volume = ec2.create_volume(
        AvailabilityZone="us-east-1a",
        Size=8,
    )

    results = find_unattached_volumes()

    assert isinstance(results, list)
    assert volume["VolumeId"] in results


@mock_aws
def test_eip_result_schema():
    """Validate the schema of EIP scanner results."""
    ec2 = boto3.client("ec2", region_name="us-east-1")

    address = ec2.allocate_address(Domain="vpc")

    results = find_unassociated_elastic_ips(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert isinstance(results, list)
    assert len(results) == 1

    finding = results[0]

    assert isinstance(finding, dict)
    assert "resource_type" in finding
    assert "finding" in finding
    assert "public_ip" in finding
    assert finding["resource_type"] == "elastic_ip"
    assert finding["finding"] == "unassociated"
    assert finding["public_ip"] == address["PublicIp"]