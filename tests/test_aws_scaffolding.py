import boto3
from moto import mock_aws


@mock_aws
def test_s3_mock_scaffolding():
    """Verify that moto can mock an AWS S3 service."""
    s3 = boto3.client("s3", region_name="us-east-1")

    bucket_name = "test-auditor-bucket"
    s3.create_bucket(Bucket=bucket_name)

    response = s3.list_buckets()

    bucket_names = [bucket["Name"] for bucket in response["Buckets"]]

    assert bucket_name in bucket_names