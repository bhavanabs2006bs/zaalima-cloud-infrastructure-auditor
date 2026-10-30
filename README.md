# Cloud Infrastructure Auditor & Cost Optimizer

A Python CLI tool for auditing AWS and GCP cloud infrastructure, identifying potentially underutilized resources, generating reports, and previewing cleanup actions.

## Features

- AWS scanning:
  - Unattached EBS volumes
  - Unassociated Elastic IP addresses
  - Underutilized EC2 instances using CloudWatch CPU metrics
- GCP resource scanning
- Region and resource-type filters
- Estimated monthly savings
- Report display and sorting
- CSV and JSON exports
- Cleanup dry-run and confirmation
- Cleanup audit logging

## Requirements

- Python 3.9 or later
- pip
- AWS credentials for AWS scans
- Google Cloud credentials for GCP scans

## Installation

```powershell
py -m pip install -e .
```

## CLI Help

```powershell
py -m cloud_auditor.cli --help
```

## AWS Scan

```powershell
py -m cloud_auditor.cli scan aws --region ap-south-1 --output audit_report.json
```

## GCP Scan

Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID.

```powershell
py -m cloud_auditor.cli scan gcp --project YOUR_PROJECT_ID --output gcp_audit_report.json
```

## View a Report

```powershell
py -m cloud_auditor.cli report audit_report.json
```

## Cleanup Preview

```powershell
py -m cloud_auditor.cli cleanup audit_report.json
```

Cleanup runs in dry-run mode by default. Review proposed actions carefully before considering execution.

## Run Tests

```powershell
py -m pytest -q
```