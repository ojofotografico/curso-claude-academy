# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AWS security lab for the Claude Academy course. Starting from two intentionally vulnerable files (`lambda_function.py` and `main.tf`), the lab demonstrates how to identify and fix common AWS security issues. All code in the repo reflects the corrected, production-ready state.

## Commands

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the performance benchmark suite:
```bash
python benchmark.py
```

There is no build step, test runner, or linter configured. The benchmark in `benchmark.py` mocks boto3 and exercises `sanitize_event` and `validate_user_id` in isolation using `timeit` and `cProfile`.

## Architecture

### `lambda_function.py`
AWS Lambda handler that fetches a user record from DynamoDB. Key design decisions:
- `SENSITIVE_FIELDS` set and `sanitize_event()` mask `password`, `credit_card`, `token`, `secret` before any logging — prevents PCI-DSS/GDPR leakage in CloudWatch.
- `_USER_ID_RE` is a module-level pre-compiled regex (`^[a-zA-Z0-9_-]{1,64}$`) to avoid recompilation on every invocation.
- `validate_user_id()` enforces type and format before the DynamoDB key lookup.
- Logger uses `%s`-style lazy formatting so `sanitize_event()` is not called when INFO level is disabled.

### `main.tf`
Terraform configuration for a production S3 bucket. Three resources work together:
1. `aws_s3_bucket` — bucket definition.
2. `aws_s3_bucket_public_access_block` — all four Block Public Access flags enabled.
3. `aws_s3_bucket_policy` — cross-account policy scoped to `s3:GetObject` and `s3:ListBucket` only, with an explicit IAM ARN principal (no wildcards).

### `benchmark.py`
Standalone performance profiler. Patches `boto3` at import time so it runs without AWS credentials. Reports `timeit` averages and a `cProfile` breakdown for the sanitization, validation, and full handler paths.
