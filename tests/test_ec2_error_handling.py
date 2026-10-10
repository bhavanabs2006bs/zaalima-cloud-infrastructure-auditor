
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


def test_ec2_scanner_handles_empty_reservations():
    """Verify EC2 scanner handles empty reservations."""
    ec2 = Mock()
    ec2.meta.region_name = "us-east-1"
    ec2.get_paginator.return_value.paginate.return_value = [
        {"Reservations": []}
    ]

    findings = find_ec2_instances(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert findings == []


def test_ec2_scanner_handles_multiple_reservations():
    """Verify EC2 scanner processes multiple reservations."""
    ec2 = Mock()
    ec2.meta.region_name = "us-east-1"
    ec2.get_paginator.return_value.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-11111111111111111",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "running"},
                        }
                    ]
                },
                {
                    "Instances": [
                        {
                            "InstanceId": "i-22222222222222222",
                            "InstanceType": "t2.small",
                            "State": {"Name": "stopped"},
                        }
                    ]
                },
            ]
        }
    ]

    findings = find_ec2_instances(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert len(findings) == 2
    assert findings[0]["resource_id"] == "i-11111111111111111"
    assert findings[1]["resource_id"] == "i-22222222222222222"
    assert findings[0]["state"] == "running"
    assert findings[1]["state"] == "stopped"
