#!/usr/bin/env python3
"""Batch checking example — processing sensor streams.

Demonstrates parallel batch checking for high-throughput
constraint validation on streaming sensor data.
"""

import time
import random
from flux_constraint import ConstraintEngine

print("=" * 60)
print("Batch Constraint Checking — Sensor Stream Processing")
print("=" * 60)

# Create engine with battery monitoring constraints
engine = ConstraintEngine.from_preset("battery")
print(f"\nBattery monitoring: {engine.count} constraints")

# Generate synthetic sensor data (simulating 1 second of readings at 10kHz)
stream_size = 10_000
sensor_data = [random.gauss(40, 15) for _ in range(stream_size)]
sensor_data_int = [int(v) for v in sensor_data]

print(f"\nSensor stream: {stream_size} readings (simulated 10kHz, 1 second)")
print(f"Value range: [{min(sensor_data_int)}, {max(sensor_data_int)}]")

# Sequential batch check
print("\n--- Sequential Processing ---")
start = time.perf_counter()
results_seq = engine.check_batch(sensor_data_int)
elapsed_seq = time.perf_counter() - start

violations_seq = sum(1 for row in results_seq if not all(r.pass_ for r in row))
print(f"  Time: {elapsed_seq*1000:.2f} ms")
print(f"  Violations: {violations_seq}/{stream_size}")
print(f"  Rate: {stream_size / elapsed_seq:,.0f} checks/sec")

# Parallel batch check
print("\n--- Parallel Processing (rayon) ---")
start = time.perf_counter()
results_par = engine.check_batch_parallel(sensor_data_int)
elapsed_par = time.perf_counter() - start

violations_par = sum(1 for row in results_par if not all(r.pass_ for r in row))
print(f"  Time: {elapsed_par*1000:.2f} ms")
print(f"  Violations: {violations_par}/{stream_size}")
print(f"  Rate: {stream_size / elapsed_par:,.0f} checks/sec")

# Verify sequential == parallel
assert violations_seq == violations_par, "Sequential and parallel results differ!"
print(f"\n  ✓ Results match: {violations_seq} violations")

# Speedup
if elapsed_par > 0:
    speedup = elapsed_seq / elapsed_par
    print(f"  Parallel speedup: {speedup:.2f}x")

# Large-scale benchmark
print("\n--- Large-Scale Benchmark ---")
for n in [1_000, 10_000, 100_000, 1_000_000]:
    data = [random.randint(-50, 120) for _ in range(n)]
    start = time.perf_counter()
    results = engine.check_batch_parallel(data)
    elapsed = time.perf_counter() - start
    violations = sum(1 for row in results if not all(r.pass_ for r in row))
    rate = n / elapsed
    print(f"  {n:>10,} values: {elapsed*1000:>8.2f} ms, {rate:>12,.0f} checks/sec, {violations} violations")

print("\n" + "=" * 60)
