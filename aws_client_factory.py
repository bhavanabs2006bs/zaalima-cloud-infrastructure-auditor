
from __future__ import annotations

from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    ProfileNotFound,
)


AWS_RETRY_CONFIG = Config(
    retries={
        "mode": "standard",
        "max_attempts": 4,
    }
)


def get_session(
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
) -> boto3.Session:
    """Create an AWS session using the standard boto3 credential chain."""
    return boto3.Session(
        profile_name=profile_name,
        region_name=region_name,
    )


def get_client(
    service_name: str,
    region_name: Optional[str] = None,
    profile_name: Optional[str] = None,
    role_arn: Optional[str] = None,
    external_id: Optional[str] = None,
):
    """Create an AWS client with centralized retry configuration."""
    session = get_session(
        profile_name=profile_name,
        region_name=region_name,
    )

    if role_arn:
        sts = session.client(
            "sts",
            config=AWS_RETRY_CONFIG,
        )

        assume_kwargs = {
            "RoleArn": role_arn,
            "RoleSessionName": "CloudAuditorSession",
        }

        if external_id:
            assume_kwargs["ExternalId"] = external_id

        credentials = sts.assume_role(
            **assume_kwargs
        )["Credentials"]

        session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=region_name,
        )

    return session.client(
        service_name,
        config=AWS_RETRY_CONFIG,
    )


def validate_credentials(
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate AWS credentials by requesting the caller identity."""
    try:
        sts_client = get_client(
            service_name="sts",
            profile_name=profile_name,
            region_name=region_name,
        )
        identity = sts_client.get_caller_identity()

        return (
            True,
            f"AWS credentials are valid for account {identity['Account']}.",
        )

    except (NoCredentialsError, PartialCredentialsError):
        return (
            False,
            "AWS credentials are missing or incomplete. "
            "Configure a supported credential source.",
        )

    except ProfileNotFound:
        return (
            False,
            "The requested AWS profile was not found. "
            "Check your AWS profile name and configuration.",
        )

    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        return (
            False,
            "AWS rejected the identity request "
            f"(error code: {code}). Check credentials and IAM permissions.",
        )

    except BotoCoreError as exc:
        return (
            False,
            "AWS credential validation failed because of an SDK error "
            f"({type(exc).__name__}).",
        )
