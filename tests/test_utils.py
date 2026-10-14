import pytest
from botocore.exceptions import ClientError

from cloud_auditor.utils import (
    estimate_ebs_monthly_cost,
    estimate_eip_monthly_cost,
    estimate_ec2_monthly_cost,
    with_backoff,
)


def test_ebs_cost_scales_with_size():
    assert estimate_ebs_monthly_cost(100) > estimate_ebs_monthly_cost(10)


def test_eip_cost_is_fixed():
    assert estimate_eip_monthly_cost() > 0


def test_ec2_cost_known_family():
    assert estimate_ec2_monthly_cost("t3.micro") > 0
    assert estimate_ec2_monthly_cost("unknown.type") > 0  # falls back to default


def test_with_backoff_retries_on_throttle(monkeypatch):
    calls = {"n": 0}

    @with_backoff(max_retries=2, base_delay=0)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise ClientError({"Error": {"Code": "Throttling"}}, "DescribeVolumes")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 2


def test_with_backoff_raises_non_throttle_immediately():
    @with_backoff(max_retries=3, base_delay=0)
    def always_fails():
        raise ClientError({"Error": {"Code": "AccessDenied"}}, "DescribeVolumes")

    with pytest.raises(ClientError):
        always_fails()
