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