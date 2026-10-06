from auditor.reporting import display_findings


def test_display_findings_with_results(capsys):
    """Verify findings are displayed correctly."""
    findings = [
        {
            "resource": "EC2",
            "finding": "underutilized",
        }
    ]

    display_findings("Test Findings", findings)

    captured = capsys.readouterr()

    assert "Test Findings" in captured.out
    assert "underutilized" in captured.out


def test_display_findings_empty(capsys):
    """Verify empty findings display a suitable message."""
    display_findings("Test Findings", [])

    captured = capsys.readouterr()

    assert "No findings detected." in captured.out