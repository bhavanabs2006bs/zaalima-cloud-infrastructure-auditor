from scan_results import build_scan_results, count_findings


def test_scanner_outputs_are_preserved_in_scan_results():
    ebs_findings = [
        {
            "resource_type": "ebs_volume",
            "resource_id": "vol-test",
            "region": "us-east-1",
            "finding": "unattached",
        }
    ]

    eip_findings = [
        {
            "resource_type": "elastic_ip",
            "resource_id": "eipalloc-test",
            "region": "us-east-1",
            "finding": "unassociated",
        }
    ]

    ec2_findings = [
        {
            "resource_type": "ec2_instance",
            "resource_id": "i-test",
            "region": "us-east-1",
            "finding": "underutilized",
            "average_cpu_14_days": 3.2,
        }
    ]

    results = build_scan_results(
        ebs_findings=ebs_findings,
        eip_findings=eip_findings,
        ec2_findings=ec2_findings,
    )

    assert results["ebs_volumes"] == ebs_findings
    assert results["elastic_ips"] == eip_findings
    assert results["ec2_instances"] == ec2_findings


def test_scan_result_counts_match_scanner_outputs():
    results = {
        "ebs_volumes": [
            {"resource_id": "vol-1"},
            {"resource_id": "vol-2"},
        ],
        "elastic_ips": [
            {"resource_id": "eip-1"},
        ],
        "ec2_instances": [
            {"resource_id": "i-1"},
            {"resource_id": "i-2"},
            {"resource_id": "i-3"},
        ],
    }

    counts = count_findings(results)

    assert counts["ebs_volumes"] == 2
    assert counts["elastic_ips"] == 1
    assert counts["ec2_instances"] == 3


def test_report_totals_match_raw_scan_findings():
    raw_scan = {
        "ebs_volumes": [
            {
                "resource_type": "ebs_volume",
                "resource_id": "vol-001",
                "finding": "unattached",
            },
            {
                "resource_type": "ebs_volume",
                "resource_id": "vol-002",
                "finding": "unattached",
            },
        ],
        "elastic_ips": [
            {
                "resource_type": "elastic_ip",
                "resource_id": "eip-001",
                "finding": "unassociated",
            }
        ],
        "ec2_instances": [
            {
                "resource_type": "ec2_instance",
                "resource_id": "i-001",
                "finding": "underutilized",
            },
            {
                "resource_type": "ec2_instance",
                "resource_id": "i-002",
                "finding": "underutilized",
            },
            {
                "resource_type": "ec2_instance",
                "resource_id": "i-003",
                "finding": "underutilized",
            },
        ],
    }

    report_counts = count_findings(raw_scan)

    assert report_counts["ebs_volumes"] == len(
        raw_scan["ebs_volumes"]
    )
    assert report_counts["elastic_ips"] == len(
        raw_scan["elastic_ips"]
    )
    assert report_counts["ec2_instances"] == len(
        raw_scan["ec2_instances"]
    )


def test_empty_raw_scan_produces_zero_report_totals():
    raw_scan = {
        "ebs_volumes": [],
        "elastic_ips": [],
        "ec2_instances": [],
    }

    report_counts = count_findings(raw_scan)

    assert report_counts == {
        "ebs_volumes": 0,
        "elastic_ips": 0,
        "ec2_instances": 0,
    }