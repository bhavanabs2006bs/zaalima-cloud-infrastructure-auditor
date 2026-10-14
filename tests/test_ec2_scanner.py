from datetime import datetime, timedelta, timezone

from ec2_scanner import (
    LOOKBACK_DAYS,
    MAX_QUERIES_PER_REQUEST,
    find_underutilized_instances,
    get_cpu_utilizations,
)


OLD_LAUNCH_TIME = datetime.now(timezone.utc) - timedelta(days=30)


class FakeCloudWatch:
    def __init__(self):
        self.calls = 0
        self.requests = []

    def get_metric_data(self, **kwargs):
        self.calls += 1
        self.requests.append(kwargs)

        return {
            "MetricDataResults": [
                {"Id": "cpu_0", "Values": [2.0, 4.0]},
                {"Id": "cpu_1", "Values": [6.0, 8.0]},
            ]
        }


def test_cpu_metrics_are_fetched_in_one_batch():
    cloudwatch = FakeCloudWatch()

    result = get_cpu_utilizations(
        ["i-001", "i-002"],
        cloudwatch_client=cloudwatch,
    )

    assert result["i-001"] == 3.0
    assert result["i-002"] == 7.0
    assert cloudwatch.calls == 1


def test_cloudwatch_request_uses_fourteen_day_window():
    cloudwatch = FakeCloudWatch()

    get_cpu_utilizations(
        ["i-001", "i-002"],
        cloudwatch_client=cloudwatch,
    )

    request = cloudwatch.requests[0]

    assert request["EndTime"] - request["StartTime"] == timedelta(
        days=LOOKBACK_DAYS
    )
    assert request["MetricDataQueries"][0]["MetricStat"]["Period"] == 86400


class FakeEC2:
    def __init__(self, instances=None):
        self.meta = type(
            "Meta",
            (),
            {"region_name": "us-east-1"},
        )()
        self.instances = instances or [
            {
                "InstanceId": "i-under",
                "InstanceType": "t3.micro",
                "State": {"Name": "running"},
                "LaunchTime": OLD_LAUNCH_TIME,
            },
            {
                "InstanceId": "i-boundary",
                "InstanceType": "t3.micro",
                "State": {"Name": "running"},
                "LaunchTime": OLD_LAUNCH_TIME,
            },
            {
                "InstanceId": "i-normal",
                "InstanceType": "t3.micro",
                "State": {"Name": "running"},
                "LaunchTime": OLD_LAUNCH_TIME,
            },
        ]

    def get_paginator(self, operation_name):
        assert operation_name == "describe_instances"

        class FakePaginator:
            def __init__(self, instances):
                self.instances = instances

            def paginate(self):
                return [
                    {
                        "Reservations": [
                            {"Instances": self.instances}
                        ]
                    }
                ]

        return FakePaginator(self.instances)


class ThresholdCloudWatch:
    def get_metric_data(self, **kwargs):
        return {
            "MetricDataResults": [
                {"Id": "cpu_0", "Values": [3.0, 4.0] * 7},
                {"Id": "cpu_1", "Values": [5.0] * 14},
                {"Id": "cpu_2", "Values": [7.0, 8.0] * 7},
            ]
        }


def test_underutilized_threshold_is_below_5_percent():
    findings = find_underutilized_instances(
        ec2_client=FakeEC2(),
        cloudwatch_client=ThresholdCloudWatch(),
    )

    finding_ids = [finding["resource_id"] for finding in findings]

    assert "i-under" in finding_ids
    assert "i-boundary" not in finding_ids
    assert "i-normal" not in finding_ids

    underutilized = next(
        finding for finding in findings
        if finding["resource_id"] == "i-under"
    )
    assert underutilized["cpu_datapoints_14_days"] == 14
    assert underutilized["average_cpu_14_days"] == 3.5


class NoDataCloudWatch:
    def get_metric_data(self, **kwargs):
        return {
            "MetricDataResults": [
                {"Id": query["Id"], "Values": []}
                for query in kwargs["MetricDataQueries"]
            ]
        }


def test_instances_without_cpu_data_are_not_flagged():
    findings = find_underutilized_instances(
        ec2_client=FakeEC2(),
        cloudwatch_client=NoDataCloudWatch(),
    )

    assert findings == []


class InsufficientDataCloudWatch:
    def get_metric_data(self, **kwargs):
        return {
            "MetricDataResults": [
                {"Id": query["Id"], "Values": [1.0, 2.0]}
                for query in kwargs["MetricDataQueries"]
            ]
        }


def test_instances_with_fewer_than_fourteen_datapoints_are_not_flagged():
    findings = find_underutilized_instances(
        ec2_client=FakeEC2(),
        cloudwatch_client=InsufficientDataCloudWatch(),
    )

    assert findings == []


class BatchCloudWatch:
    def __init__(self):
        self.calls = 0
        self.query_counts = []

    def get_metric_data(self, **kwargs):
        self.calls += 1
        self.query_counts.append(len(kwargs["MetricDataQueries"]))

        return {
            "MetricDataResults": [
                {
                    "Id": query["Id"],
                    "Values": [10.0],
                }
                for query in kwargs["MetricDataQueries"]
            ]
        }


def test_cloudwatch_requests_are_split_into_batches():
    instance_ids = [f"i-{index:04d}" for index in range(501)]
    cloudwatch = BatchCloudWatch()

    result = get_cpu_utilizations(
        instance_ids,
        cloudwatch_client=cloudwatch,
    )

    assert cloudwatch.calls == 2
    assert cloudwatch.query_counts == [
        MAX_QUERIES_PER_REQUEST,
        1,
    ]
    assert len(result) == 501
    assert result["i-0000"] == 10.0
    assert result["i-0500"] == 10.0


def test_stopped_instances_are_not_flagged():
    instances = [
        {
            "InstanceId": "i-stopped",
            "InstanceType": "t3.micro",
            "State": {"Name": "stopped"},
            "LaunchTime": OLD_LAUNCH_TIME,
        }
    ]

    findings = find_underutilized_instances(
        ec2_client=FakeEC2(instances),
        cloudwatch_client=ThresholdCloudWatch(),
    )

    assert findings == []


def test_recently_launched_instances_are_not_flagged():
    recent_launch = datetime.now(timezone.utc) - timedelta(days=3)
    instances = [
        {
            "InstanceId": "i-new",
            "InstanceType": "t3.micro",
            "State": {"Name": "running"},
            "LaunchTime": recent_launch,
        }
    ]

    findings = find_underutilized_instances(
        ec2_client=FakeEC2(instances),
        cloudwatch_client=ThresholdCloudWatch(),
    )

    assert findings == []


def test_instances_without_launch_time_are_not_flagged():
    instances = [
        {
            "InstanceId": "i-unknown-launch",
            "InstanceType": "t3.micro",
            "State": {"Name": "running"},
            "LaunchTime": None,
        }
    ]

    findings = find_underutilized_instances(
        ec2_client=FakeEC2(instances),
        cloudwatch_client=ThresholdCloudWatch(),
    )

    assert findings == []
