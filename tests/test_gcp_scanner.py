
from unittest.mock import MagicMock, patch

from cloud_auditor.scanners.gcp_scanner import (
    _gb_from_bytes_str,
    scan_unattached_gcp_disks,
    scan_idle_gcp_addresses,
    scan_underutilized_gcp_instances,
)


def test_gb_from_bytes_str():
    assert _gb_from_bytes_str("50") == 50
    assert _gb_from_bytes_str(None) == 0
    assert _gb_from_bytes_str("invalid") == 0


@patch("google.cloud.compute_v1.DisksClient")
def test_finds_unattached_disk(mock_client_class):
    disk = MagicMock()
    disk.users = []
    disk.name = "test-disk"
    disk.size_gb = "50"
    disk.type_ = "zones/us-central1-a/diskTypes/pd-standard"

    response = MagicMock()
    response.disks = [disk]

    mock_client = mock_client_class.return_value
    mock_client.aggregated_list.return_value = [
        ("zones/us-central1-a", response)
    ]

    findings = scan_unattached_gcp_disks(
        credentials=MagicMock(),
        project="test-project",
    )

    assert len(findings) == 1
    assert findings[0].resource_id == "test-disk"
    assert findings[0].resource_type == "gcp_disk"


@patch("google.cloud.compute_v1.AddressesClient")
def test_finds_reserved_static_ip(mock_client_class):
    address = MagicMock()
    address.status = "RESERVED"
    address.name = "test-ip"
    address.address = "203.0.113.10"

    response = MagicMock()
    response.addresses = [address]

    mock_client = mock_client_class.return_value
    mock_client.aggregated_list.return_value = [
        ("regions/us-central1", response)
    ]

    findings = scan_idle_gcp_addresses(
        credentials=MagicMock(),
        project="test-project",
    )

    assert len(findings) == 1
    assert findings[0].resource_id == "test-ip"
    assert findings[0].resource_type == "gcp_static_ip"


@patch("cloud_auditor.scanners.gcp_scanner._get_avg_cpu_gcp")
@patch("google.cloud.compute_v1.InstancesClient")
def test_finds_underutilized_instance(mock_client_class, mock_cpu):
    instance = MagicMock()
    instance.status = "RUNNING"
    instance.id = 12345
    instance.name = "test-instance"
    instance.machine_type = (
        "zones/us-central1-a/machineTypes/e2-medium"
    )

    response = MagicMock()
    response.instances = [instance]

    mock_client = mock_client_class.return_value
    mock_client.aggregated_list.return_value = [
        ("zones/us-central1-a", response)
    ]
    mock_cpu.return_value = 2.0

    findings = scan_underutilized_gcp_instances(
        credentials=MagicMock(),
        project="test-project",
    )

    assert len(findings) == 1
    assert findings[0].resource_id == "test-instance"
    assert findings[0].resource_type == "gcp_instance"
    assert findings[0].metadata["avg_cpu_pct"] == 2.0
