
from unittest.mock import MagicMock, patch

from cloud_auditor.scanners import Finding
from cloud_auditor.scanners.aws_ec2 import (
    scan_underutilized_ec2_instances,
    _suggest_downsize,
)


def test_suggest_downsize():
    assert _suggest_downsize("t3.xlarge") == "t3.large"
    assert _suggest_downsize("t3.large") == "t3.medium"
    assert _suggest_downsize("t3.small") is None


@patch("cloud_auditor.scanners.aws_ec2._get_avg_cpu")
@patch("cloud_auditor.scanners.aws_ec2._describe_running_instances")
def test_finds_underutilized_instance(mock_instances, mock_cpu):
    mock_instances.return_value = [
        {
            "InstanceId": "i-test123",
            "InstanceType": "t3.large",
            "Tags": [{"Key": "Name", "Value": "TestServer"}],
        }
    ]
    mock_cpu.return_value = 2.0

    findings = scan_underutilized_ec2_instances(
        session=MagicMock(),
        region="us-east-1",
        account_id="123456789012",
    )

    assert len(findings) == 1
    assert findings[0].resource_id == "i-test123"
    assert findings[0].resource_type == "ec2_instance"
    assert findings[0].metadata["avg_cpu_pct"] == 2.0


@patch("cloud_auditor.scanners.aws_ec2._get_avg_cpu")
@patch("cloud_auditor.scanners.aws_ec2._describe_running_instances")
def test_skips_instance_with_high_cpu(mock_instances, mock_cpu):
    mock_instances.return_value = [
        {
            "InstanceId": "i-busy123",
            "InstanceType": "t3.large",
            "Tags": [],
        }
    ]
    mock_cpu.return_value = 60.0

    findings = scan_underutilized_ec2_instances(
        session=MagicMock(),
        region="us-east-1",
        account_id="123456789012",
    )

    assert findings == []


@patch("cloud_auditor.scanners.aws_ec2._get_avg_cpu")
@patch("cloud_auditor.scanners.aws_ec2._describe_running_instances")
def test_skips_instance_without_cpu_data(mock_instances, mock_cpu):
    mock_instances.return_value = [
        {
            "InstanceId": "i-nodata123",
            "InstanceType": "t3.large",
            "Tags": [],
        }
    ]
    mock_cpu.return_value = None

    findings = scan_underutilized_ec2_instances(
        session=MagicMock(),
        region="us-east-1",
        account_id="123456789012",
    )

    assert findings == []
