import boto3


def get_ec2_instances(region="us-east-1"):
    """Return EC2 instance information from AWS."""
    ec2 = boto3.client("ec2", region_name=region)

    response = ec2.describe_instances()

    instances = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append({
                "instance_id": instance["InstanceId"],
                "instance_type": instance["InstanceType"],
                "state": instance["State"]["Name"],
            })

    return instances
def get_s3_buckets(region="us-east-1"):
    """Return S3 bucket information from AWS."""
    s3 = boto3.client("s3", region_name=region)

    response = s3.list_buckets()

    buckets = []

    for bucket in response["Buckets"]:
        buckets.append({
            "name": bucket["Name"],
            "creation_date": bucket["CreationDate"],
        })

    return buckets