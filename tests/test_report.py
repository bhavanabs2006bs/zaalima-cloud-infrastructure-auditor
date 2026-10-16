
import csv
import json

import pytest

from cloud_auditor.report import export, export_csv, export_json
from cloud_auditor.scanners import Finding


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
