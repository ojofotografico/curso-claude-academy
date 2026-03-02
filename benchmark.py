"""
Benchmarks and profiling for lambda_function.py

Mocks boto3/DynamoDB so we can benchmark pure Python logic without AWS calls.
"""
import json
import re
import timeit
import cProfile
import pstats
import io
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Patch boto3 before importing lambda_function so the module-level
# `dynamodb = boto3.resource('dynamodb')` doesn't fail.
# ---------------------------------------------------------------------------
mock_table = MagicMock()
mock_table.get_item.return_value = {
    'Item': {'user_id': 'user123', 'email': 'user@example.com'}
}
mock_dynamodb = MagicMock()
mock_dynamodb.Table.return_value = mock_table

import sys
sys.modules['boto3'] = MagicMock(resource=MagicMock(return_value=mock_dynamodb))

import lambda_function  # noqa: E402  (import after patching)

# Re-point the table used inside the module to our mock
lambda_function.table = mock_table

# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------
SAMPLE_EVENT_CLEAN = {
    'user_id': 'user123',
    'action': 'get_profile',
    'region': 'us-east-1',
}

SAMPLE_EVENT_SENSITIVE = {
    'user_id': 'user123',
    'password': 's3cr3t',
    'token': 'abc.def.ghi',
    'action': 'login',
}

SAMPLE_CONTEXT = MagicMock()

VALID_IDS = ['user123', 'alice_bob', 'id-9999', 'A' * 64]
INVALID_IDS = ['', 'bad user', 'a' * 65, 'DROP TABLE']

ITERATIONS = 100_000

# ---------------------------------------------------------------------------
# Individual benchmarks
# ---------------------------------------------------------------------------

def bench_sanitize_event_clean(n=ITERATIONS):
    t = timeit.timeit(
        lambda: lambda_function.sanitize_event(SAMPLE_EVENT_CLEAN),
        number=n,
    )
    return t, n

def bench_sanitize_event_sensitive(n=ITERATIONS):
    t = timeit.timeit(
        lambda: lambda_function.sanitize_event(SAMPLE_EVENT_SENSITIVE),
        number=n,
    )
    return t, n

def bench_validate_user_id_valid(n=ITERATIONS):
    t = timeit.timeit(
        lambda: lambda_function.validate_user_id('user123'),
        number=n,
    )
    return t, n

def bench_validate_user_id_invalid(n=ITERATIONS):
    """Measures the cost of the unhappy path (ValueError)."""
    def _run():
        try:
            lambda_function.validate_user_id('bad user!')
        except ValueError:
            pass
    t = timeit.timeit(_run, number=n)
    return t, n

def bench_lambda_handler(n=10_000):
    t = timeit.timeit(
        lambda: lambda_function.lambda_handler(SAMPLE_EVENT_CLEAN, SAMPLE_CONTEXT),
        number=n,
    )
    return t, n

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all():
    benchmarks = [
        ("sanitize_event (no sensitive fields)", bench_sanitize_event_clean),
        ("sanitize_event (with sensitive fields)", bench_sanitize_event_sensitive),
        ("validate_user_id (valid id)",           bench_validate_user_id_valid),
        ("validate_user_id (invalid id)",         bench_validate_user_id_invalid),
        ("lambda_handler (full path)",            bench_lambda_handler),
    ]

    results = []
    print("\n" + "=" * 65)
    print(f"{'Benchmark':<42} {'Iters':>8}  {'Total(s)':>9}  {'us/call':>9}")
    print("=" * 65)
    for label, fn in benchmarks:
        total, n = fn()
        per_call_us = (total / n) * 1_000_000
        results.append((label, n, total, per_call_us))
        print(f"{label:<42} {n:>8}  {total:>9.3f}  {per_call_us:>9.3f}")
    print("=" * 65)
    return results

# ---------------------------------------------------------------------------
# cProfile deep-dive on the worst offenders
# ---------------------------------------------------------------------------

def profile_function(label, fn, n=50_000):
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(n):
        try:
            fn()
        except Exception:
            pass
    pr.disable()

    stream = io.StringIO()
    ps = pstats.Stats(pr, stream=stream).sort_stats('cumulative')
    ps.print_stats(15)

    print(f"\n--- cProfile: {label} ({n} iterations) ---")
    print(stream.getvalue())

if __name__ == '__main__':
    print("\n### BENCHMARK RESULTS ###")
    results = run_all()

    # Sort by per-call cost descending to find the worst performers
    worst = sorted(results, key=lambda r: r[3], reverse=True)

    print("\n### PROFILING WORST PERFORMERS ###")
    # Profile the top-2 slowest
    targets = [
        ("validate_user_id (valid)",   lambda: lambda_function.validate_user_id('user123')),
        ("validate_user_id (invalid)", lambda: lambda_function.validate_user_id('bad user!')),
        ("sanitize_event (sensitive)", lambda: lambda_function.sanitize_event(SAMPLE_EVENT_SENSITIVE)),
        ("lambda_handler",             lambda: lambda_function.lambda_handler(SAMPLE_EVENT_CLEAN, SAMPLE_CONTEXT)),
    ]
    for label, fn in targets:
        profile_function(label, fn)
