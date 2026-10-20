
import json
import subprocess

import pytest

from cloud_auditor.cleanup import (
    _parse_cleanup_command,
    execute_cleanup,
    load_findings_from_report,
    print_dry_run,
)


def test_load_findings_from_json_list(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps([{"resource_id": "test-1"}]), encoding="utf-8")

    assert load_findings_from_report(str(report)) == [
        {"resource_id": "test-1"}
    ]


def test_load_findings_from_json_object(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps({"findings": [{"resource_id": "test-2"}]}),
        encoding="utf-8",
    )

    assert load_findings_from_report(str(report)) == [
        {"resource_id": "test-2"}
    ]


def test_invalid_report_format(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"wrong": []}), encoding="utf-8")

    with pytest.raises(ValueError):
        load_findings_from_report(str(report))


def test_dry_run_does_not_execute_commands(monkeypatch):
    def unexpected_run(*args, **kwargs):
        raise AssertionError("Dry-run must never execute commands")

    monkeypatch.setattr(subprocess, "run", unexpected_run)

    print_dry_run([
        {
            "provider": "aws",
            "resource_type": "ebs",
            "resource_id": "vol-test",
            "reason": "Test only",
            "cleanup_action": "review",
        }
    ])


def test_confirmation_required():
    with pytest.raises(PermissionError):
        execute_cleanup(
            [{"cleanup_action": "aws ec2 terminate-instances"}],
            confirm_token="no",
        )


def test_rejects_non_cloud_command():
    with pytest.raises(ValueError):
        _parse_cleanup_command("python delete_everything.py")


def test_rejects_multiline_command():
    with pytest.raises(ValueError):
        _parse_cleanup_command("aws ec2 describe-instances\naws s3 rm s3://bucket")


def test_accepts_aws_cli_command():
    assert _parse_cleanup_command(
        "aws ec2 describe-instances"
    ) == ["aws", "ec2", "describe-instances"]
