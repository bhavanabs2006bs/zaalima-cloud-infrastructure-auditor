import boto3
from moto import mock_aws

from cloud_auditor.scanners.aws_eip import scan_unassociated_eips


@mock_aws
def test_finds_unassociated_eip_only():
    region = "us-east-1"
    session = boto3.Session(region_name=region)
    ec2 = session.client("ec2", region_name=region)

    unassociated = ec2.allocate_address(Domain="vpc")

    instance = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t3.micro"
    )["Instances"][0]
    associated = ec2.allocate_address(Domain="vpc")
    ec2.associate_address(
        AllocationId=associated["AllocationId"], InstanceId=instance["InstanceId"]
    )

    findings = scan_unassociated_eips(session, region, account_id="123456789012")

    ids_found = {f.resource_id for f in findings}
    assert unassociated["AllocationId"] in ids_found
    assert associated["AllocationId"] not in ids_found
