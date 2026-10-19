
import csv
import json

import pytest
from cloud_auditor.report import render_findings_table
from cloud_auditor.report import export, export_csv, export_json
from cloud_auditor.scanners import Finding
from io import StringIO
from rich.console import Console

def sample_finding():
    return Finding(
        provider="aws",
        resource_type="ebs",
        resource_id="vol-test-123",
        region="us-east-1",
        reason="Unattached volume",
        estimated_monthly_savings=10.50,
        cleanup_action="delete_volume",
        metadata={"size_gb": 100},
        severity="low",
        account_or_project="test-account",
    )


def test_export_json_creates_valid_report(tmp_path):
    finding = sample_finding()
    output_file = tmp_path / "report.json"

    result = export_json([finding], str(output_file))

    assert output_file.exists()
    assert result == str(output_file)

    data = json.loads(output_file.read_text())

    assert data["finding_count"] == 1
    assert data["estimated_total_monthly_savings"] == 10.50
    assert data["findings"][0]["resource_id"] == "vol-test-123"
    assert "generated_at" in data


def test_export_csv_creates_valid_report(tmp_path):
    finding = sample_finding()
    output_file = tmp_path / "report.csv"

    result = export_csv([finding], str(output_file))

    assert output_file.exists()
    assert result == str(output_file)

    with output_file.open("r", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["provider"] == "aws"
    assert rows[0]["resource_id"] == "vol-test-123"
    assert float(rows[0]["estimated_monthly_savings"]) == 10.50
    assert json.loads(rows[0]["metadata"]) == {"size_gb": 100}


def test_export_selects_json_by_extension(tmp_path):
    output_file = tmp_path / "report.json"

    result = export([sample_finding()], str(output_file))

    assert result == str(output_file)
    assert json.loads(output_file.read_text())["finding_count"] == 1


def test_export_selects_csv_by_extension(tmp_path):
    output_file = tmp_path / "report.csv"

    result = export([sample_finding()], str(output_file))

    assert result == str(output_file)

    with output_file.open("r", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1


def test_export_rejects_unsupported_extension(tmp_path):
    output_file = tmp_path / "report.txt"

    with pytest.raises(ValueError, match="Unsupported export format"):
        export([sample_finding()], str(output_file))

def test_render_empty_findings(capsys):
    render_findings_table([])
    output = capsys.readouterr().out

    assert "No wasteful or misconfigured resources found." in output




def test_render_findings_table_sorts_by_savings():
    from cloud_auditor import report

    low_savings = sample_finding()
    high_savings = Finding(
        provider="aws",
        resource_type="ec2",
        resource_id="i-test-high",
        region="us-east-1",
        reason="Low CPU utilization",
        estimated_monthly_savings=50.0,
        cleanup_action="review_instance",
        metadata={},
        severity="high",
        account_or_project="test-account",
    )

    # Test sorting directly, without relying on terminal formatting.
    sorted_findings = sorted(
        [low_savings, high_savings],
        key=lambda finding: finding.estimated_monthly_savings,
        reverse=True,
    )

    assert sorted_findings[0].resource_id == "i-test-high"
    assert sorted_findings[1].resource_id == "vol-test-123"
    assert sum(
        finding.estimated_monthly_savings for finding in sorted_findings
    ) == 60.50
