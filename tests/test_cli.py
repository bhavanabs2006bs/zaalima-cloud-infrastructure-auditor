
from typer.testing import CliRunner

from cloud_auditor.cli import app
from cloud_auditor.scanners import Finding

runner = CliRunner()


def sample_finding(resource_type="ebs"):
    return Finding(
        provider="aws",
        resource_type=resource_type,
        resource_id="test-resource-123",
        region="us-east-1",
        reason="Test finding",
        estimated_monthly_savings=10.50,
        cleanup_action="review",
        metadata={},
        severity="low",
        account_or_project="test-account",
    )


def test_invalid_aws_resource_type():
    result = runner.invoke(
        app,
        ["scan", "aws", "--resource-type", "invalid"],
    )

    assert result.exit_code != 0
    assert "Choose one of" in result.output
