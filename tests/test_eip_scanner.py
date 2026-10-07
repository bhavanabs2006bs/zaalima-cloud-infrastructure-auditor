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
from unittest.mock import Mock
from botocore.exceptions import NoCredentialsError, BotoCoreError


def test_eip_scanner_handles_no_credentials():
    """Verify EIP scanner converts credential errors to RuntimeError."""
    ec2 = Mock()
    ec2.describe_addresses.side_effect = NoCredentialsError()

    try:
        find_unassociated_elastic_ips(
            ec2_client=ec2,
            region_name="us-east-1",
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Unable to scan Elastic IPs" in str(exc)


def test_eip_scanner_handles_boto_core_error():
    """Verify EIP scanner converts BotoCoreError to RuntimeError."""
    ec2 = Mock()
    ec2.describe_addresses.side_effect = BotoCoreError()

    try:
        find_unassociated_elastic_ips(
            ec2_client=ec2,
            region_name="us-east-1",
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Unable to scan Elastic IPs" in str(exc)    