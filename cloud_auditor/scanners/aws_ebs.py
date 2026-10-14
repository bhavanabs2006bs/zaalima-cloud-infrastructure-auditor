"""Scan for unattached (orphaned) EBS volumes."""

from __future__ import annotations

from typing import List

from cloud_auditor.scanners import Finding
from cloud_auditor.utils import estimate_ebs_monthly_cost, with_backoff


@with_backoff()
def _describe_available_volumes(session, region: str):
    ec2 = session.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_volumes")
    volumes = []
    for page in paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}]):
        volumes.extend(page.get("Volumes", []))
    return volumes


def scan_unattached_ebs_volumes(session, region: str, account_id: str) -> List[Finding]:
    """A volume in the 'available' state has no attachments and is billed
    for storage with zero compute value — a classic orphaned resource.
    """
    findings: List[Finding] = []
    for vol in _describe_available_volumes(session, region):
        size_gb = vol.get("Size", 0)
        vol_id = vol["VolumeId"]
        name_tag = next(
            (t["Value"] for t in vol.get("Tags", []) if t["Key"] == "Name"), None
        )
        findings.append(
            Finding(
                provider="aws",
                region=region,
                resource_type="ebs_volume",
                resource_id=vol_id,
                reason=f"Unattached EBS volume ({size_gb} GiB, {vol.get('VolumeType', 'unknown')})"
                + (f", name='{name_tag}'" if name_tag else ""),
                estimated_monthly_savings=estimate_ebs_monthly_cost(size_gb),
                cleanup_action=(
                    f"aws ec2 delete-volume --volume-id {vol_id} --region {region}"
                ),
                metadata={
                    "size_gb": size_gb,
                    "volume_type": vol.get("VolumeType"),
                    "create_time": str(vol.get("CreateTime")),
                    "name_tag": name_tag,
                },
                severity="medium",
                account_or_project=account_id,
            )
        )
    return findings
