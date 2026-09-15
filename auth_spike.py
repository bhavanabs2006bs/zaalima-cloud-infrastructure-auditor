import boto3

try:
    session = boto3.Session(profile_name="default")
    sts = session.client("sts")
    identity = sts.get_caller_identity()

    print("Authentication Successful")
    print("Account:", identity["Account"])

except Exception as e:
    print("Authentication Failed")
    print(e)