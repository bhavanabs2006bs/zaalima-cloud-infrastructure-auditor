# Week 1 Wrap-Up — Member 3

## Role
Member 3 — Reporting & Testing Lead

## Week 1 Work

### Day 1
Set up the project structure, Rich reporting support, and README skeleton.

### Day 2
Configured the PyYAML configuration loader for project settings.

### Day 3
Set up pytest and Moto test scaffolding for AWS-related testing.

### Day 4
Worked on AWS discovery testing and EC2 discovery functionality.

### Day 5
Worked on AWS S3 discovery and verified S3 functionality using Moto.

### Day 6
Added unit tests for the region-mapping utility, including:
- Parsing comma-separated AWS regions.
- Handling whitespace in region arguments.
- Automatic region discovery when no regions are supplied.

### Day 7
Added unit tests for API rate-limit handling, including:
- Retrying AWS throttling errors.
- Verifying exponential backoff behavior.
- Ensuring non-throttling errors are not retried.

## Testing Status

The Week 1 testing setup uses pytest, Moto, boto3, and unittest.mock.

All implemented tests were verified locally before committing.