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