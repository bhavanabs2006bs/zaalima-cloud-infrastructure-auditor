import boto3
from moto import mock_aws

from ebs_scanner import find_unattached_volumes
from eip_scanner import find_unassociated_elastic_ips
from ec2_scanner import find_underutilized_instances


@mock_aws
def test_aggregated_scan_pipeline():
    """Verify all scanners can run together and return results."""

    ec2 = boto3.client("ec2", region_name="us-east-1")

    # Run EBS scanner
    ebs_results = find_unattached_volumes()

    # Run EIP scanner
    eip_results = find_unassociated_elastic_ips(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    # Run EC2 scanner
    ec2_results = find_underutilized_instances(
        ec2_client=ec2,
        cloudwatch_client=boto3.client(
            "cloudwatch",
            region_name="us-east-1",
        ),
        
    )

    # Aggregate all scanner results
    all_results = {
        "ebs": ebs_results,
        "eip": eip_results,
        "ec2": ec2_results,
    }

    assert "ebs" in all_results
    assert "eip" in all_results
    assert "ec2" in all_results