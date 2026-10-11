
# AWS Authentication Prototype

## Objective

Evaluate how the Cloud Infrastructure Auditor can authenticate
with AWS through Boto3 without hardcoding access credentials.

## Authentication options

1. Default credential chain:
   Boto3 checks the supported credential sources configured
   in the environment.

2. Named AWS profile:
   A profile can be selected through the shared client factory
   using the `profile_name` argument.

3. IAM role assumption:
   The client factory supports assuming an IAM role through STS.
   An external ID can optionally be supplied.

## Prototype implementation

The `auth_spike.py` script calls STS GetCallerIdentity through
`aws_client_factory.py`.

A successful request confirms that AWS accepted the credentials
for this identity request. It does not prove that the identity
has permission to scan or delete every resource.

## Security considerations

- Do not hardcode access keys, secret keys, or session tokens.
- Prefer supported credential providers, named profiles,
  or temporary role credentials.
- Grant only the IAM permissions the application needs.
- Do not print secret credentials or session tokens.
- Keep AWS requests out of module import time.

## Error handling

The prototype handles missing or incomplete credentials,
AWS service errors, and AWS SDK errors with understandable
messages. Authentication failures return a non-zero exit code.

## Retry handling

The shared AWS client factory configures Botocore retries.
Retry behaviour and its tests will be reviewed separately
under Day 6 and Day 7.

## Verification status

The code structure has been reviewed. Successful authentication
must be verified in an AWS environment with valid credentials.
Unit tests should also verify failure cases without requiring
a real AWS account.

## Credential Validation

The shared AWS client factory provides a `validate_credentials()`
function that checks credentials by requesting the caller identity
from AWS STS.

The function returns a success flag and a readable message. It
handles missing or incomplete credentials, unknown AWS profiles,
AWS service errors, and Botocore SDK errors.

Automated tests use mocked STS responses to check successful
identity validation, missing-credential handling, and forwarding
of profile and region settings. These tests do not require a real
AWS account.

Successful authentication against a real AWS environment has not
been verified in this development environment.
