# Scanner Output Contract

The AWS scanners return a list of dictionaries.

This output is the data contract between the
Cloud & Scanning component and the Reporting
& Testing component.

## Common fields

- resource_type
- resource_id
- region
- finding
- tags

## EBS fields

- state
- size_gb
- volume_type
- encrypted
- availability_zone
- created_at

## Elastic IP fields

- public_ip
- domain
- network_border_group

## Example

```json
[
  {
    "resource_type": "ebs_volume",
    "resource_id": "vol-example",
    "region": "us-east-1",
    "finding": "unattached",
    "state": "available",
    "size_gb": 50,
    "volume_type": "gp3",
    "encrypted": true
  }
]
## EC2 fields

- instance_type
- state
- launch_time
- average_cpu_14_days
- threshold
- lookback_days