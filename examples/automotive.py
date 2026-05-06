#!/usr/bin/env python3
"""ISO 26262 Automotive Example — ASIL-D Constraint Checking.

Demonstrates constraint checking for an automotive ECU with:
- Vehicle speed monitoring
- Brake pressure validation
- Steering angle limits
- Engine RPM protection

Reference: ISO 26262 Part 4 (Product Development at System Level)
"""

from flux_constraint import ConstraintEngine

print("=" * 60)
print("ISO 26262 ASIL-D Automotive Constraint Example")
print("=" * 60)

# Create automotive constraint engine from preset
engine = ConstraintEngine.from_preset("automotive")
print(f"\nEngine: {engine}")

# Simulate a driving scenario
print("\n--- Normal Driving Scenario ---")
scenarios = [
    (80, "Highway cruise"),
    (120, "Autobahn"),
    (5, "Parking"),
    (0, "Stopped"),
]

for speed, desc in scenarios:
    results = engine.check(speed)
    status = "PASS" if all(r.pass_ for r in results) else "FAIL"
    fails = [r.name for r in results if not r.pass_]
    fail_str = f" FAILED: {', '.join(fails)}" if fails else ""
    print(f"  Speed {speed:4d} km/h ({desc:15s}): {status}{fail_str}")

# Edge case: saturated values
print("\n--- INT8 Saturation Edge Cases ---")
edge_cases = [
    (300, "Over speed limit → saturates to 127"),
    (-50, "Reverse → saturates to -127"),
    (127, "Exactly at INT8 max"),
]

for speed, desc in edge_cases:
    results = engine.check(speed)
    for r in results:
        if r.original_value != r.saturated_value:
            print(f"  {desc}: {r.original_value} → {r.saturated_value} ({r.name}: {'PASS' if r.pass_ else 'FAIL'})")

# Batch check for statistical validation
print("\n--- Batch Statistical Check (1000 values) ---")
import random
random.seed(42)
test_values = [random.randint(-200, 300) for _ in range(1000)]
results = engine.check_batch(test_values)

pass_count = 0
fail_count = 0
for row in results:
    if all(r.pass_ for r in row):
        pass_count += 1
    else:
        fail_count += 1

print(f"  1000 random values: {pass_count} pass, {fail_count} fail ({pass_count/10:.1f}% pass rate)")

# Benchmark
print("\n--- Performance ---")
rate, ms = engine.benchmark(1000)
print(f"  Throughput: {rate:,.0f} checks/sec")
print(f"  Per-check latency: {ms / (1000 * 1000):.3f} µs")

print("\n" + "=" * 60)
