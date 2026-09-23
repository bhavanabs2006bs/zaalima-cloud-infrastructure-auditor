import boto3

from moto import mock_aws

from auditor.aws_discovery import get_ec2_instances, get_s3_buckets


@mock_aws
def test_get_ec2_instances():
    ec2 = boto3.client("ec2", region_name="us-east-1")

    ec2.run_instances(
        ImageId="ami-12345678",
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",
    )

    instances = get_ec2_instances("us-east-1")

    assert len(instances) == 1
    assert instances[0]["instance_type"] == "t2.micro"
    assert instances[0]["state"] == "running"
@mock_aws
def test_get_s3_buckets():
    s3 = boto3.client("s3", region_name="us-east-1")

    s3.create_bucket(Bucket="test-auditor-bucket")

    buckets = get_s3_buckets("us-east-1")

    assert len(buckets) == 1
    assert buckets[0]["name"] == "test-auditor-bucket"