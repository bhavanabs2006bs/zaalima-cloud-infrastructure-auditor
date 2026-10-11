import importlib

import auth_spike


from unittest.mock import Mock, patch

from botocore.exceptions import NoCredentialsError

from aws_client_factory import validate_credentials


@patch("aws_client_factory.get_client")
def test_validation_succeeds_with_valid_identity(mock_get_client):
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/test",
        "UserId": "test-user",
    }
    mock_get_client.return_value = mock_sts

    success, message = validate_credentials()

    assert success is True
    assert "123456789012" in message


@patch("aws_client_factory.get_client")
def test_validation_reports_missing_credentials(mock_get_client):
    mock_sts = Mock()
    mock_sts.get_caller_identity.side_effect = NoCredentialsError()
    mock_get_client.return_value = mock_sts

    success, message = validate_credentials()

    assert success is False
    assert "missing or incomplete" in message


@patch("aws_client_factory.get_client")
def test_validation_uses_requested_profile(mock_get_client):
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/test",
        "UserId": "test-user",
    }
    mock_get_client.return_value = mock_sts

    validate_credentials(profile_name="development", region_name="us-east-1")

    mock_get_client.assert_called_once_with(
        service_name="sts",
        profile_name="development",
        region_name="us-east-1",
    )
import importlib
from unittest.mock import MagicMock, patch

import auth_spike


def test_authentication_does_not_print_credentials(capsys):
    fake_client = MagicMock()
    fake_client.get_caller_identity.return_value = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:user/test",
        "UserId": "test-user",
    }

    with patch.object(
        auth_spike, "get_client", return_value=fake_client
    ):
        assert auth_spike.check_aws_authentication() is True

    output = capsys.readouterr().out

    assert "AWS authentication successful." in output
    assert "temporary-secret-key" not in output
    assert "temporary-session-token" not in output
    assert "aws_secret_access_key" not in output
    assert "aws_session_token" not in output


def test_importing_auth_spike_does_not_call_aws():
    with patch.object(auth_spike, "get_client") as mocked_get_client:
        importlib.reload(auth_spike)

    mocked_get_client.assert_not_called()


def test_authentication_failure_does_not_print_exception_secrets(capsys):
    fake_client = MagicMock()
    fake_client.get_caller_identity.side_effect = Exception(
        "temporary-secret-key"
    )

    with patch.object(
        auth_spike, "get_client", return_value=fake_client
    ):
        try:
            auth_spike.check_aws_authentication()
        except Exception:
            pass

    output = capsys.readouterr().out
    assert "temporary-secret-key" not in output