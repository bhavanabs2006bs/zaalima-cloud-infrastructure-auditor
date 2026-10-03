from ec2_scanner import (
    find_underutilized_instances,
    get_cpu_utilizations,
)


class FakeCloudWatch:
    def __init__(self):
        self.calls = 0

    def get_metric_data(self, **kwargs):
        self.calls += 1

        return {
            "MetricDataResults": [
                {
                    "Id": "cpu_0",
                    "Values": [2.0, 4.0],
                },
                {
                    "Id": "cpu_1",
                    "Values": [6.0, 8.0],
                },
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


class FakeEC2:
    def __init__(self):
        self.meta = type(
            "Meta",
            (),
            {"region_name": "us-east-1"},
        )()

    def get_paginator(self, operation_name):

        class FakePaginator:
            def paginate(self):

                return [
                    {
                        "Reservations": [
                            {
                                "Instances": [
                                    {
                                        "InstanceId": "i-under",
                                        "InstanceType": "t3.micro",
                                        "State": {
                                            "Name": "running"
                                        },
                                        "LaunchTime": None,
                                    },
                                    {
                                        "InstanceId": "i-boundary",
                                        "InstanceType": "t3.micro",
                                        "State": {
                                            "Name": "running"
                                        },
                                        "LaunchTime": None,
                                    },
                                    {
                                        "InstanceId": "i-normal",
                                        "InstanceType": "t3.micro",
                                        "State": {
                                            "Name": "running"
                                        },
                                        "LaunchTime": None,
                                    },
                                ]
                            }
                        ]
                    }
                ]

        return FakePaginator()


class ThresholdCloudWatch:
    def get_metric_data(self, **kwargs):

        return {
            "MetricDataResults": [
                {
                    "Id": "cpu_0",
                    "Values": [3.0, 4.0],
                },
                {
                    "Id": "cpu_1",
                    "Values": [5.0, 5.0],
                },
                {
                    "Id": "cpu_2",
                    "Values": [7.0, 8.0],
                },
            ]
        }


def test_underutilized_threshold_is_below_5_percent():

    findings = find_underutilized_instances(
        ec2_client=FakeEC2(),
        cloudwatch_client=ThresholdCloudWatch(),
    )

    finding_ids = [
        finding["resource_id"]
        for finding in findings
    ]

    assert "i-under" in finding_ids
    assert "i-boundary" not in finding_ids
    assert "i-normal" not in finding_ids


class NoDataCloudWatch:
    def get_metric_data(self, **kwargs):

        return {
            "MetricDataResults": [
                {
                    "Id": "cpu_0",
                    "Values": [],
                },
                {
                    "Id": "cpu_1",
                    "Values": [],
                },
                {
                    "Id": "cpu_2",
                    "Values": [],
                },
            ]
        }


def test_instances_without_cpu_data_are_not_flagged():

    findings = find_underutilized_instances(
        ec2_client=FakeEC2(),
        cloudwatch_client=NoDataCloudWatch(),
    )

    assert findings == []


class BatchCloudWatch:
    def __init__(self):
        self.calls = 0
        self.query_counts = []

    def get_metric_data(self, **kwargs):

        self.calls += 1

        self.query_counts.append(
            len(kwargs["MetricDataQueries"])
        )

        results = []

        for query in kwargs["MetricDataQueries"]:
            results.append(
                {
                    "Id": query["Id"],
                    "Values": [10.0],
                }
            )

        return {
            "MetricDataResults": results
        }


def test_cloudwatch_requests_are_split_into_batches():

    instance_ids = [
        f"i-{index:04d}"
        for index in range(501)
    ]

    cloudwatch = BatchCloudWatch()

    result = get_cpu_utilizations(
        instance_ids,
        cloudwatch_client=cloudwatch,
    )

    assert cloudwatch.calls == 2

    assert cloudwatch.query_counts == [
        500,
        1,
    ]

    assert len(result) == 501

    assert result["i-0000"] == 10.0
    assert result["i-0500"] == 10.0