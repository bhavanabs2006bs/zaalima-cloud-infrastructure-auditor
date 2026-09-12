# AWS Authentication Research

## Authentication Methods Studied

1. AWS Access Key and Secret Key
2. AWS CLI Configured Profile
3. IAM Roles

## Preferred Method

AWS CLI Profile Authentication

Reason:
- More secure than hardcoding credentials
- Easy to manage
- Recommended by AWS

## Boto3 Library

Boto3 is the AWS SDK for Python and allows interaction with AWS services.

## Testing Result

Boto3 was installed successfully.

Test Result:
Authentication Failed - Unable to locate credentials

Reason:
AWS credentials have not been configured locally.

Next Step:
Configure AWS CLI credentials or use IAM role authentication.
