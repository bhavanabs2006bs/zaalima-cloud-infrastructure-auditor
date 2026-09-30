import boto3
from moto import mock_aws

from eip_scanner import find_unassociated_elastic_ips


@mock_aws
def test_find_unassociated_elastic_ips():
    ec2 = boto3.client("ec2", region_name="us-east-1")

    address = ec2.allocate_address(Domain="vpc")

    findings = find_unassociated_elastic_ips(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert len(findings) == 1
    assert findings[0]["resource_type"] == "elastic_ip"
    assert findings[0]["finding"] == "unassociated"
    assert findings[0]["public_ip"] == address["PublicIp"]


@mock_aws
def test_no_unassociated_elastic_ips():
    ec2 = boto3.client("ec2", region_name="us-east-1")

    findings = find_unassociated_elastic_ips(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert findings == []