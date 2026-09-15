## AWS Profile Authentication Testing

Implemented profile-based authentication using:

session = boto3.Session(profile_name="default")

Result:
Authentication Failed - The config profile (default) could not be found.

Reason:
AWS CLI profile has not been configured on the local machine.

Next Step:
Configure AWS credentials using AWS CLI and retest authentication.