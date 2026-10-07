from unittest.mock import Mock

from botocore.exceptions import NoCredentialsError, BotoCoreError

from ec2_scanner import find_ec2_instances, get_cpu_utilizations


def test_ec2_scanner_handles_no_credentials():
    """Verify EC2 scanner converts credential errors to RuntimeError."""
    ec2 = Mock()
    ec2.get_paginator.side_effect = NoCredentialsError()

    try:
        find_ec2_instances(
            ec2_client=ec2,
            region_name="us-east-1",
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Unable to scan EC2 instances" in str(exc)


def test_ec2_scanner_handles_boto_core_error():
    """Verify EC2 scanner converts BotoCoreError to RuntimeError."""
    ec2 = Mock()
    ec2.get_paginator.side_effect = BotoCoreError()

    try:
        find_ec2_instances(
            ec2_client=ec2,
            region_name="us-east-1",
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Unable to scan EC2 instances" in str(exc)


def test_cpu_utilization_handles_no_credentials():
    """Verify CPU metrics convert credential errors to RuntimeError."""
    cloudwatch = Mock()
    cloudwatch.get_metric_data.side_effect = NoCredentialsError()

    try:
        get_cpu_utilizations(
            ["i-1234567890abcdef0"],
            cloudwatch_client=cloudwatch,
            region_name="us-east-1",
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Unable to read batch CPU metrics" in str(exc)


def test_cpu_utilization_handles_boto_core_error():
    """Verify CPU metrics convert BotoCoreError to RuntimeError."""
    cloudwatch = Mock()
    cloudwatch.get_metric_data.side_effect = BotoCoreError()

    try:
        get_cpu_utilizations(
            ["i-1234567890abcdef0"],
            cloudwatch_client=cloudwatch,
            region_name="us-east-1",
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Unable to read batch CPU metrics" in str(exc)