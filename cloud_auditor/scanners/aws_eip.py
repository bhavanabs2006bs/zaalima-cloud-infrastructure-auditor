"""Scan for unassociated Elastic IPs (AWS bills for idle EIPs)."""

from __future__ import annotations

from typing import List

from cloud_auditor.scanners import Finding
from cloud_auditor.utils import estimate_eip_monthly_cost, with_backoff


@with_backoff()
def _describe_addresses(session, region: str):
    ec2 = session.client("ec2", region_name=region)
    resp = ec2.describe_addresses()
    return resp.get("Addresses", [])


def scan_unassociated_eips(session, region: str, account_id: str) -> List[Finding]:
    findings: List[Finding] = []
    for addr in _describe_addresses(session, region):
        if addr.get("AssociationId") or addr.get("InstanceId"):
            continue  # in use — skip

        alloc_id = addr.get("AllocationId")
        public_ip = addr.get("PublicIp")
        resource_id = alloc_id or public_ip

        findings.append(
            Finding(
                provider="aws",
                region=region,
                resource_type="elastic_ip",
                resource_id=resource_id,
                reason=f"Elastic IP {public_ip} is allocated but not associated with any resource",
                estimated_monthly_savings=estimate_eip_monthly_cost(),
                cleanup_action=(
                    f"aws ec2 release-address --allocation-id {alloc_id} --region {region}"
                    if alloc_id
                    else f"aws ec2 release-address --public-ip {public_ip} --region {region}"
                ),
                metadata={"public_ip": public_ip, "allocation_id": alloc_id},
                severity="low",
                account_or_project=account_id,
            )
        )
    return findings
