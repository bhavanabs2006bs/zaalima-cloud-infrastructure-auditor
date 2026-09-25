# EBS Scanner Notes

Purpose:
Identify unattached EBS volumes that may be generating unnecessary AWS costs.

Logic:
- Retrieve all EBS volumes.
- Check Attachments list.
- If Attachments is empty, mark as unattached.

Current Status:
Scanner implementation completed.

Testing Status:
AWS testing pending because credentials are not configured.