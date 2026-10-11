
"""Prototype AWS authentication using the shared Boto3 client factory."""

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

from aws_client_factory import get_client


def check_aws_authentication() -> bool:
    """Verify AWS credentials by calling STS GetCallerIdentity."""
    try:
        sts_client = get_client("sts")
        identity = sts_client.get_caller_identity()

        print("AWS authentication successful.")
        print(f"Account ID: {identity['Account']}")
        print(f"ARN: {identity['Arn']}")
        return True

    except (NoCredentialsError, PartialCredentialsError):
        print(
            "AWS authentication failed: credentials are missing "
            "or incomplete. Check your AWS profile or credential setup."
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get(
            "Code", "Unknown"
        )
        print(
            "AWS authentication failed: AWS rejected the request "
            f"(error code: {error_code}). Check your credentials "
            "and IAM permissions."
        )
    except BotoCoreError as exc:
        print(
            "AWS authentication failed because of an AWS SDK error: "
            f"{type(exc).__name__}."
        )
    except Exception as exc:
        print(
            "AWS authentication failed because of an unexpected error: "
            f"{type(exc).__name__}."
        )
    return False


def main() -> int:
    """Run the authentication prototype."""
    return 0 if check_aws_authentication() else 1


if __name__ == "__main__":
    raise SystemExit(main())
