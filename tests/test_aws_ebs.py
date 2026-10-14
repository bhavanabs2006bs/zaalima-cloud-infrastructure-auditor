import boto3
from moto import mock_aws

from cloud_auditor.scanners.aws_ebs import scan_unattached_ebs_volumes


@mock_aws
def test_finds_unattached_volume_only():
    region = "us-east-1"
    session = boto3.Session(region_name=region)
    ec2 = session.client("ec2", region_name=region)

    # An unattached volume - should be flagged.
    orphan = ec2.create_volume(Size=100, AvailabilityZone=f"{region}a")

    # An attached volume - should NOT be flagged.
    ami = ec2.describe_images()["Images"]
    instance = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t3.micro"
    )["Instances"][0]
    attached = ec2.create_volume(Size=50, AvailabilityZone=f"{region}a")
    ec2.attach_volume(
        VolumeId=attached["VolumeId"], InstanceId=instance["InstanceId"], Device="/dev/sdf"
    )

    findings = scan_unattached_ebs_volumes(session, region, account_id="123456789012")

    ids_found = {f.resource_id for f in findings}
    assert orphan["VolumeId"] in ids_found
    assert attached["VolumeId"] not in ids_found
    assert all(f.estimated_monthly_savings > 0 for f in findings)


@mock_aws
def test_no_volumes_returns_empty():
    region = "us-west-2"
    session = boto3.Session(region_name=region)
    findings = scan_unattached_ebs_volumes(session, region, account_id="123456789012")
    assert findings == []
