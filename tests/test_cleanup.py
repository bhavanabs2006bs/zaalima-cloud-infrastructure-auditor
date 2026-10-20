
import json
import subprocess
from types import SimpleNamespace

import pytest

import cloud_auditor.cleanup as cleanup_module
from cloud_auditor.cleanup import (
    _parse_cleanup_command,
    execute_cleanup,
    load_findings_from_report,
    print_dry_run,
)


def sample_finding(action="aws ec2 describe-instances"):
    return {
        "provider": "aws",
        "resource_type": "ec2",
        "resource_id": "test-instance",
        "reason": "Test finding",
        "cleanup_action": action,
    }


def test_load_findings_from_json_list(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps([{"resource_id": "test-1"}]),
        encoding="utf-8",
    )

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


def test_report_rejects_non_dictionary_finding(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps(["invalid"]), encoding="utf-8")

    with pytest.raises(ValueError):
        load_findings_from_report(str(report))


def test_dry_run_does_not_execute_commands(monkeypatch):
    def unexpected_run(*args, **kwargs):
        raise AssertionError("Dry-run must never execute commands")

    monkeypatch.setattr(subprocess, "run", unexpected_run)

    print_dry_run([sample_finding()])


def test_confirmation_required(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(
        cleanup_module,
        "AUDIT_LOG_PATH",
        audit_path,
    )

    with pytest.raises(PermissionError):
        execute_cleanup(
            [sample_finding()],
            confirm_token="no",
        )

    records = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]

    assert records[0]["status"] == "rejected"
    assert records[0]["resource_id"] == "test-instance"


def test_rejects_non_cloud_command():
    with pytest.raises(ValueError):
        _parse_cleanup_command("python delete_everything.py")


def test_rejects_multiline_command():
    with pytest.raises(ValueError):
        _parse_cleanup_command(
            "aws ec2 describe-instances\naws s3 rm s3://bucket"
        )


def test_accepts_aws_cli_command():
    assert _parse_cleanup_command(
        "aws ec2 describe-instances"
    ) == ["aws", "ec2", "describe-instances"]


def test_audit_log_records_success(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(
        cleanup_module,
        "AUDIT_LOG_PATH",
        audit_path,
    )

    monkeypatch.setattr(
        cleanup_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="mock success"),
    )

    execute_cleanup(
        [sample_finding()],
        confirm_token="DELETE",
    )

    records = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]

    assert [record["status"] for record in records] == [
        "started",
        "success",
    ]
    assert records[-1]["resource_id"] == "test-instance"
    assert records[-1]["timestamp"]
    assert records[-1]["command"] == "aws ec2 describe-instances"


def test_audit_log_records_command_failure(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(
        cleanup_module,
        "AUDIT_LOG_PATH",
        audit_path,
    )

    def mock_failure(*args, **kwargs):
        raise subprocess.CalledProcessError(
            1,
            args[0],
            stderr="mock cloud command failure",
        )

    monkeypatch.setattr(
        cleanup_module.subprocess,
        "run",
        mock_failure,
    )

    execute_cleanup(
        [sample_finding()],
        confirm_token="DELETE",
    )

    records = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]

    assert [record["status"] for record in records] == [
        "started",
        "failed",
    ]
    assert "mock cloud command failure" in records[-1]["error"]


def test_audit_log_rejects_unsupported_command(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(
        cleanup_module,
        "AUDIT_LOG_PATH",
        audit_path,
    )

    execute_cleanup(
        [sample_finding("python unwanted_script.py")],
        confirm_token="DELETE",
    )

    records = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]

    assert len(records) == 1
    assert records[0]["status"] == "rejected"
    assert "Unsupported cleanup command" in records[0]["error"]


def test_cleanup_skips_execution_if_start_log_fails(monkeypatch):
    def fail_logging(*args, **kwargs):
        raise OSError("disk unavailable")

    def unexpected_run(*args, **kwargs):
        raise AssertionError("Command must not run if start logging fails")

    monkeypatch.setattr(cleanup_module, "_write_audit_log", fail_logging)
    monkeypatch.setattr(cleanup_module.subprocess, "run", unexpected_run)

    execute_cleanup(
        [sample_finding()],
        confirm_token="DELETE",
    )
