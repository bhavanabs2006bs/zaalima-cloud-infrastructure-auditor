from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from cloud_auditor.utils import with_backoff


def make_client_error(error_code):
    """Create a boto3-style ClientError for testing."""
    return ClientError(
        {
            "Error": {
                "Code": error_code,
                "Message": "Test error",
            }
        },
        "TestOperation",
    )


@patch("cloud_auditor.utils.time.sleep")
def test_with_backoff_retries_throttled_request(mock_sleep):
    """Verify throttled requests are retried with exponential backoff."""

    calls = {"count": 0}

    @with_backoff(max_retries=3, base_delay=1)
    def throttled_function():
        calls["count"] += 1

        if calls["count"] < 3:
            raise make_client_error("Throttling")

        return "success"

    result = throttled_function()

    assert result == "success"
    assert calls["count"] == 3

    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1)
    mock_sleep.assert_any_call(2)


@patch("cloud_auditor.utils.time.sleep")
def test_with_backoff_does_not_retry_non_throttle_error(mock_sleep):
    """Verify non-throttling AWS errors are raised immediately."""

    @with_backoff(max_retries=3, base_delay=1)
    def failing_function():
        raise make_client_error("AccessDenied")

    with pytest.raises(ClientError):
        failing_function()

    mock_sleep.assert_not_called()