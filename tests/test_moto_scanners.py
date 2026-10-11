import boto3
from moto import mock_aws

from ebs_scanner import find_unattached_volumes
from eip_scanner import find_unassociated_elastic_ips


@mock_aws
def test_eip_scanner_finds_only_unassociated_addresses(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    ec2 = boto3.client("ec2", region_name="us-east-1")

    unassociated = ec2.allocate_address(Domain="vpc")
    associated = ec2.allocate_address(Domain="vpc")

    response = ec2.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
    )
    instance_id = response["Instances"][0]["InstanceId"]

    ec2.associate_address(
        InstanceId=instance_id,
        AllocationId=associated["AllocationId"],
    )

    findings = find_unassociated_elastic_ips(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert len(findings) == 1
    assert findings[0]["resource_id"] == unassociated["AllocationId"]
    assert findings[0]["finding"] == "unassociated"
    assert findings[0]["region"] == "us-east-1"


@mock_aws
def test_ebs_scanner_finds_only_unattached_volumes(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    ec2 = boto3.client("ec2", region_name="us-east-1")

    unattached = ec2.create_volume(
        AvailabilityZone="us-east-1a",
        Size=8,
        VolumeType="gp3",
    )

    instance_response = ec2.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
    )
    instance_id = instance_response["Instances"][0]["InstanceId"]

    attached = ec2.create_volume(
        AvailabilityZone="us-east-1a",
        Size=8,
        VolumeType="gp3",
    )

    ec2.attach_volume(
        VolumeId=attached["VolumeId"],
        InstanceId=instance_id,
        Device="/dev/sdf",
    )

    findings = find_unattached_volumes(
        ec2_client=ec2,
        region_name="us-east-1",
    )

    assert len(findings) == 1
    assert findings[0]["resource_id"] == unattached["VolumeId"]
    assert findings[0]["finding"] == "unattached"
    assert findings[0]["region"] == "us-east-1"
    assert findings[0]["size_gb"] == 8
