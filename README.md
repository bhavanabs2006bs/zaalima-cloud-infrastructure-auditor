# Cloud Infrastructure Auditor & Cost Optimizer

A Python CLI tool that scans AWS infrastructure for potentially wasteful resources, including unattached EBS volumes, unassociated Elastic IP addresses, and underutilized EC2 instances.

## Features

- AWS client and credential validation support.
- Scanning for unattached EBS volumes.
- Detection of unassociated Elastic IP addresses.
- Identification of potentially underutilized EC2 instances using CloudWatch CPU metrics.
- Aggregated scan results and JSON report output.
- Explicit confirmation required by cleanup functions before destructive actions.

## Requirements

- Python 3.10 or newer.
- AWS credentials with appropriate read permissions for scanning.
- Access to the AWS services used by the selected scanners.

## Installation

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Usage

Display help:

```powershell
cloud-auditor --help
```

Scan a region:

```powershell
cloud-auditor --region us-east-1
```

Save results to a JSON file:

```powershell
cloud-auditor --region us-east-1 --output reports/scan.json
```

The scan commands require valid AWS credentials. Do not run destructive cleanup operations against real resources without reviewing the findings and explicitly authorizing the operation.

## Run tests

```powershell
python -m pytest -v
```

## Current scope

The implemented scanners target AWS. GCP scanning and standalone executable packaging should not be considered supported until implemented and tested.
