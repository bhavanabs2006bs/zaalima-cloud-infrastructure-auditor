# Changelog

## 0.1.0 — Initial development release

- Added AWS client and credential-validation support.
- Added scanning for unattached EBS volumes.
- Added scanning for unassociated Elastic IP addresses.
- Added EC2 underutilization detection using CloudWatch CPU metrics.
- Added aggregated scan results and JSON report output.
- Added explicit confirmation checks for destructive cleanup functions.
- Added a Typer-based command-line entry point.
- Added Python package installation configuration.
- Added automated scanner, cleanup, and integration tests.

### Limitations

- AWS scanning requires valid AWS credentials and appropriate permissions.
- Standalone executable packaging and clean-machine execution remain to be verified.
- GCP scanning is not included in the current implementation.
