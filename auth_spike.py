import boto3

ROLE_ARN = "arn:aws:iam::123456789012:role/TestRole"

try:
    sts = boto3.client("sts")

    response = sts.assume_role(
        RoleArn=ROLE_ARN,
        RoleSessionName="CloudAuditorSession"
    )

    print("Role assumed successfully")

except Exception as e:
    print("Role assumption failed")
    print(e)