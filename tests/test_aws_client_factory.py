from botocore.stub import Stubber

from unittest.mock import MagicMock, patch

from botocore.session import Session
from botocore.stub import Stubber


import aws_client_factory as factory


def test_get_client_uses_requested_service_region_and_retry_config():
    fake_session = MagicMock()
    fake_client = MagicMock()
    fake_session.client.return_value = fake_client

    with patch.object(factory, "get_session", return_value=fake_session) as get_session:
        client = factory.get_client(
            "ec2",
            region_name="us-east-1",
            profile_name="test-profile",
        )

    get_session.assert_called_once_with(
        profile_name="test-profile",
        region_name="us-east-1",
    )
    fake_session.client.assert_called_once_with(
        "ec2",
        config=factory.AWS_RETRY_CONFIG,
    )
    assert client is fake_client


def test_get_client_assumes_role_and_passes_external_id():
    fake_initial_session = MagicMock()
    fake_sts = MagicMock()
    fake_initial_session.client.return_value = fake_sts

    fake_sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "temporary-access-key",
            "SecretAccessKey": "temporary-secret-key",
            "SessionToken": "temporary-session-token",
        }
    }

    fake_assumed_session = MagicMock()
    fake_client = MagicMock()
    fake_assumed_session.client.return_value = fake_client

    with (
        patch.object(
            factory,
            "get_session",
            return_value=fake_initial_session,
        ),
        patch.object(
            factory.boto3,
            "Session",
            return_value=fake_assumed_session,
        ) as session_constructor,
    ):
        client = factory.get_client(
            "ec2",
            region_name="us-east-1",
            role_arn="arn:aws:iam::123456789012:role/CloudAuditorRole",
            external_id="test-external-id",
        )

    fake_sts.assume_role.assert_called_once_with(
        RoleArn="arn:aws:iam::123456789012:role/CloudAuditorRole",
        RoleSessionName="CloudAuditorSession",
        ExternalId="test-external-id",
    )

    session_constructor.assert_called_once_with(
        aws_access_key_id="temporary-access-key",
        aws_secret_access_key="temporary-secret-key",
        aws_session_token="temporary-session-token",
        region_name="us-east-1",
    )

    fake_assumed_session.client.assert_called_once_with(
        "ec2",
        config=factory.AWS_RETRY_CONFIG,
    )
    assert client is fake_client


def test_get_client_omits_external_id_when_not_provided():
    fake_initial_session = MagicMock()
    fake_sts = MagicMock()
    fake_initial_session.client.return_value = fake_sts
    fake_sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "temporary-access-key",
            "SecretAccessKey": "temporary-secret-key",
            "SessionToken": "temporary-session-token",
        }
    }

    fake_assumed_session = MagicMock()

    with (
        patch.object(
            factory,
            "get_session",
            return_value=fake_initial_session,
        ),
        patch.object(
            factory.boto3,
            "Session",
            return_value=fake_assumed_session,
        ),
    ):
        factory.get_client(
            "ec2",
            role_arn="arn:aws:iam::123456789012:role/CloudAuditorRole",
        )

    fake_sts.assume_role.assert_called_once_with(
        RoleArn="arn:aws:iam::123456789012:role/CloudAuditorRole",
        RoleSessionName="CloudAuditorSession",
    )
def test_retry_config_uses_standard_mode_and_four_attempts():
    retry_settings = factory.AWS_RETRY_CONFIG.retries

    assert retry_settings["mode"] == "standard"
    assert retry_settings["max_attempts"] == 4


def test_retry_config_is_applied_to_real_botocore_client():
    session = Session()
    client = session.create_client(
        "ec2",
        region_name="us-east-1",
        aws_access_key_id="test-access-key",
        aws_secret_access_key="test-secret-key",
        config=factory.AWS_RETRY_CONFIG,
    )

    retries = client.meta.config.retries

    assert retries["mode"] == "standard"
    assert retries["total_max_attempts"] == 5
