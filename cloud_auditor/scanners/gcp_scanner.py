
"""Google Cloud Platform resource scanners."""

from cloud_auditor.scanners import Finding
from cloud_auditor.utils import (
    estimate_ebs_monthly_cost,
    estimate_eip_monthly_cost,
)


def _gb_from_bytes_str(size_gb):
    """Convert a disk size to an integer GB value."""
    try:
        return int(float(size_gb))
    except (TypeError, ValueError):
        return 0


def scan_unattached_gcp_disks(credentials, project):
    """Find unattached GCP disks."""
    from google.cloud import compute_v1

    findings = []
    client = compute_v1.DisksClient(credentials=credentials)

    for scope, response in client.aggregated_list(project=project):
        for disk in response.disks or []:
            if disk.users:
                continue

            size_gb = _gb_from_bytes_str(disk.size_gb)
            findings.append(
                Finding(
                    provider="gcp",
                    region=scope.split("/")[-1],
                    resource_type="gcp_disk",
                    resource_id=disk.name,
                    reason="Disk is not attached to a VM.",
                    estimated_monthly_savings=estimate_ebs_monthly_cost(
                        size_gb
                    ),
                    cleanup_action=(
                        f"Review disk {disk.name} before deleting it."
                    ),
                    metadata={
                        "size_gb": size_gb,
                        "disk_type": disk.type_,
                    },
                    account_or_project=project,
                )
            )

    return findings


def scan_idle_gcp_addresses(credentials, project):
    """Find reserved GCP external IP addresses."""
    from google.cloud import compute_v1

    findings = []
    client = compute_v1.AddressesClient(credentials=credentials)

    for scope, response in client.aggregated_list(project=project):
        for address in response.addresses or []:
            if address.status != "RESERVED":
                continue

            findings.append(
                Finding(
                    provider="gcp",
                    region=scope.split("/")[-1],
                    resource_type="gcp_static_ip",
                    resource_id=address.name,
                    reason="External IP is reserved and may be unused.",
                    estimated_monthly_savings=estimate_eip_monthly_cost(),
                    cleanup_action=(
                        f"Verify address {address.name} is unused "
                        "before releasing it."
                    ),
                    metadata={
                        "address": address.address,
                        "status": address.status,
                    },
                    account_or_project=project,
                )
            )

    return findings


def _get_avg_cpu_gcp(
    credentials,
    project,
    instance_id,
    minutes=60,
):
    """Return average CPU utilization percentage, or None."""
    from datetime import datetime, timedelta, timezone

    from google.cloud import monitoring_v3

    client = monitoring_v3.MetricServiceClient(
        credentials=credentials
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=minutes)

    interval = monitoring_v3.TimeInterval(
        {
            "start_time": start_time,
            "end_time": end_time,
        }
    )

    aggregation = monitoring_v3.Aggregation(
        {
            "alignment_period": {"seconds": 60},
            "per_series_aligner": (
                monitoring_v3.Aggregation.Aligner.ALIGN_MEAN
            ),
        }
    )

    filter_string = (
        'metric.type = "compute.googleapis.com/instance/cpu/utilization" '
        'AND resource.type = "gce_instance" '
        f'AND resource.labels.instance_id = "{instance_id}"'
    )

    results = client.list_time_series(
        request={
            "name": f"projects/{project}",
            "filter": filter_string,
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            "aggregation": aggregation,
        }
    )

    values = [
        point.value.double_value * 100
        for series in results
        for point in series.points
    ]

    if not values:
        return None

    return sum(values) / len(values)


def scan_underutilized_gcp_instances(
    credentials,
    project,
    threshold=10.0,
):
    """Find running GCP instances with low CPU utilization."""
    from google.cloud import compute_v1

    findings = []
    client = compute_v1.InstancesClient(credentials=credentials)

    for scope, response in client.aggregated_list(project=project):
        for instance in response.instances or []:
            if instance.status != "RUNNING":
                continue

            avg_cpu = _get_avg_cpu_gcp(
                credentials=credentials,
                project=project,
                instance_id=str(instance.id),
            )

            if avg_cpu is None or avg_cpu >= threshold:
                continue

            findings.append(
                Finding(
                    provider="gcp",
                    region=scope.split("/")[-1],
                    resource_type="gcp_instance",
                    resource_id=instance.name,
                    reason=f"Average CPU utilization is low ({avg_cpu:.2f}%).",
                    estimated_monthly_savings=0.0,
                    cleanup_action=(
                        "Review utilization before resizing or stopping "
                        "this instance."
                    ),
                    metadata={
                        "machine_type": instance.machine_type,
                        "avg_cpu_pct": avg_cpu,
                    },
                    account_or_project=project,
                )
            )

    return findings
