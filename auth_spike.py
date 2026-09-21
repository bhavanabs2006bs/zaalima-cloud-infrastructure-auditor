import boto3
from botocore.exceptions import NoCredentialsError, ProfileNotFound

try:
    session = boto3.Session(profile_name="default")
    sts = session.client("sts")
    identity = sts.get_caller_identity()

    print("Authentication Successful")
    print("Account:", identity["Account"])

except ProfileNotFound:
    print("Error: AWS profile 'default' was not found.")

except NoCredentialsError:
    print("Error: AWS credentials not configured.")

except Exception as e:
    print("Authentication Failed")
    print(f"Unexpected error: {e}")