import boto3
from botocore.exceptions import NoCredentialsError, ProfileNotFound

try:
    session = boto3.Session(profile_name="default")

    credentials = session.get_credentials()

    if credentials is None:
        raise NoCredentialsError()

    print("Credentials found")

    sts = session.client("sts")
    identity = sts.get_caller_identity()

    print("Authentication Successful")
    print("Account:", identity["Account"])

except ProfileNotFound:
    print("Error: AWS profile 'default' not found.")

except NoCredentialsError:
    print("Error: No AWS credentials configured.")

except Exception as e:
    print("Authentication Failed")
    print(e)