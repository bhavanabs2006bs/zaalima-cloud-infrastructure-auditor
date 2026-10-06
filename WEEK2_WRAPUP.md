# Week 2 Wrap-up

## Overview

Week 2 focused on testing and validating the Cloud Infrastructure Auditor.
The main goal was to improve test coverage, verify AWS scanner behavior using
Moto, handle edge cases, and validate the aggregated scanning process.

## Work Completed

### Day 8 – EBS Scanner Tests

Added Moto-based tests for the EBS scanner to verify detection of
unattached EBS volumes and empty results.

### Day 9 – EIP Scanner Tests

Added tests for the Elastic IP scanner to verify detection of
unassociated Elastic IP addresses.

### Day 10 – Edge Case Tests

Added tests for empty AWS accounts and multiple AWS regions.

### Day 11 – CloudWatch Scanner Tests

Added tests to verify CloudWatch-based CPU utilization scanning behavior.

### Day 12 – Threshold Edge Cases

Added tests to validate scanner behavior for underutilized instances
and empty accounts.

### Day 13 – Aggregated Scan Test

Added an end-to-end test to verify that multiple AWS scanners can run
together and that their results can be aggregated correctly.

### Day 14 – Schema Validation

Added tests to validate the structure and expected fields of scanner results.

## Testing Result

The complete test suite was executed successfully.

**Final Result: 18 tests passed**

## Conclusion

Week 2 successfully improved the reliability and test coverage of the
Cloud Infrastructure Auditor. AWS services were tested using Moto without
requiring real AWS resources. Edge cases, threshold-related behavior,
aggregated scanning, and result schemas were also validated.

All planned Week 2 testing tasks were completed successfully.