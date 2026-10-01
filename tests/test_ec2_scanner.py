from ec2_scanner import get_cpu_utilizations


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

    # Both instances were handled by one CloudWatch request
    assert cloudwatch.calls == 1