import csv
import io
import json

from scan_results import build_scan_results


def get_sample_scan_results():
    ebs_findings = [
        {
            "resource_type": "ebs_volume",
            "resource_id": "vol-001",
            "region": "us-east-1",
            "finding": "unattached",
        }
    ]

    eip_findings = [
        {
            "resource_type": "elastic_ip",
            "resource_id": "eip-001",
            "region": "us-east-1",
            "finding": "unassociated",
        }
    ]

    ec2_findings = [
        {
            "resource_type": "ec2_instance",
            "resource_id": "i-001",
            "region": "us-east-1",
            "finding": "underutilized",
        }
    ]

    return build_scan_results(
        ebs_findings=ebs_findings,
        eip_findings=eip_findings,
        ec2_findings=ec2_findings,
    )


def get_multi_region_scan_results():
    ebs_findings = [
        {
            "resource_type": "ebs_volume",
            "resource_id": "vol-east-001",
            "region": "us-east-1",
            "finding": "unattached",
        },
        {
            "resource_type": "ebs_volume",
            "resource_id": "vol-west-001",
            "region": "us-west-2",
            "finding": "unattached",
        },
    ]

    eip_findings = [
        {
            "resource_type": "elastic_ip",
            "resource_id": "eip-east-001",
            "region": "us-east-1",
            "finding": "unassociated",
        },
        {
            "resource_type": "elastic_ip",
            "resource_id": "eip-west-001",
            "region": "us-west-2",
            "finding": "unassociated",
        },
    ]

    ec2_findings = [
        {
            "resource_type": "ec2_instance",
            "resource_id": "i-east-001",
            "region": "us-east-1",
            "finding": "underutilized",
        },
        {
            "resource_type": "ec2_instance",
            "resource_id": "i-west-001",
            "region": "us-west-2",
            "finding": "underutilized",
        },
    ]

    return build_scan_results(
        ebs_findings=ebs_findings,
        eip_findings=eip_findings,
        ec2_findings=ec2_findings,
    )


def test_json_export_preserves_scan_data():
    scan_results = get_sample_scan_results()

    exported_json = json.dumps(scan_results)
    imported_data = json.loads(exported_json)

    assert imported_data == scan_results


def test_csv_export_preserves_resource_ids_and_findings():
    scan_results = get_sample_scan_results()

    records = (
        scan_results["ebs_volumes"]
        + scan_results["elastic_ips"]
        + scan_results["ec2_instances"]
    )

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=[
            "resource_type",
            "resource_id",
            "region",
            "finding",
        ],
    )

    writer.writeheader()
    writer.writerows(records)

    output.seek(0)

    rows = list(csv.DictReader(output))

    assert len(rows) == len(records)

    for original, exported in zip(records, rows):
        assert exported["resource_type"] == original["resource_type"]
        assert exported["resource_id"] == original["resource_id"]
        assert exported["region"] == original["region"]
        assert exported["finding"] == original["finding"]


def test_multi_region_export_preserves_all_records():
    scan_results = get_multi_region_scan_results()

    records = (
        scan_results["ebs_volumes"]
        + scan_results["elastic_ips"]
        + scan_results["ec2_instances"]
    )

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=[
            "resource_type",
            "resource_id",
            "region",
            "finding",
        ],
    )

    writer.writeheader()
    writer.writerows(records)

    output.seek(0)

    rows = list(csv.DictReader(output))

    assert len(rows) == 6

    exported_ids = {
        row["resource_id"]
        for row in rows
    }

    expected_ids = {
        "vol-east-001",
        "vol-west-001",
        "eip-east-001",
        "eip-west-001",
        "i-east-001",
        "i-west-001",
    }

    assert exported_ids == expected_ids


def test_multi_region_export_preserves_region_information():
    scan_results = get_multi_region_scan_results()

    records = (
        scan_results["ebs_volumes"]
        + scan_results["elastic_ips"]
        + scan_results["ec2_instances"]
    )

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=[
            "resource_type",
            "resource_id",
            "region",
            "finding",
        ],
    )

    writer.writeheader()
    writer.writerows(records)

    output.seek(0)

    rows = list(csv.DictReader(output))

    regions = {
        row["region"]
        for row in rows
    }

    assert regions == {
        "us-east-1",
        "us-west-2",
    }