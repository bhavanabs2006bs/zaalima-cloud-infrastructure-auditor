from ec2_scanner import get_cpu_utilizations


def test_get_cpu_utilizations_with_no_instances():
    """Verify CPU utilization returns an empty dictionary for no instances."""
    result = get_cpu_utilizations([])

    assert result == {}