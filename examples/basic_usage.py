#!/usr/bin/env python3
"""Basic usage example — FLUX Constraint Engine from Python.

This works with both the native Rust extension and the pure Python fallback.
"""

from flux_constraint import (
    Constraint, ConstraintEngine, check,
    battery, automotive, aviation,
)

print("=" * 60)
print("FLUX Constraint Engine — Basic Usage")
print("=" * 60)

# 1. Quick single check
print("\n--- Quick Check ---")
result = check(60, 15, 55)
print(f"check(60, lo=15, hi=55) → pass={result.pass_}, sat_val={result.saturated_value}")

result = check(-10, 0, 100)
print(f"check(-10, lo=0, hi=100) → pass={result.pass_}, sat_val={result.saturated_value}")

result = check(200, 0, 100)
print(f"check(200, lo=0, hi=100) → pass={result.pass_}, sat_val={result.saturated_value}")

# 2. Constraint object
print("\n--- Constraint Object ---")
c = Constraint(15, 55, "battery_temp", 3)
print(f"Created: {c}")
r = c.check(60)
print(f"check(60) → {r}")

# 3. ConstraintEngine with custom constraints
print("\n--- Custom Engine ---")
engine = ConstraintEngine()
engine.add_constraint(15, 55, "battery_temp", 3)
engine.add_constraint(0, 100, "charge_rate", 2)
engine.add_constraint(-40, 85, "ambient", 1)
print(f"Engine: {engine}")

for value in [20, 60, -10, 200]:
    results = engine.check(value)
    passes = sum(1 for r in results if r.pass_)
    print(f"  check({value:4d}): {passes}/{len(results)} pass")

# 4. Batch checking
print("\n--- Batch Check ---")
values = [20, 30, 40, 50, 60, 70, 80, 100, 127, 200]
batch = engine.check_batch(values)
for val, row in zip(values, batch):
    status = " ".join("✓" if r.pass_ else "✗" for r in row)
    print(f"  {val:4d}: {status}")

# 5. Industry presets
print("\n--- Industry Presets ---")
for factory, name in [(battery, "Battery"), (automotive, "Automotive"), (aviation, "Aviation")]:
    e = factory()
    rate, ms = e.benchmark(100)
    print(f"  {name:12s}: {e.count} constraints, {rate:,.0f} checks/sec")

# 6. Benchmark comparison
print("\n--- Benchmark ---")
engine = ConstraintEngine.from_preset("battery")
rate, ms = engine.benchmark(500)
print(f"Battery preset: {rate:,.0f} checks/sec ({ms:.1f} ms for 500 iterations)")
print(f"That's {rate/1_000_000:.1f}M constraint evaluations per second")

print("\n" + "=" * 60)
print("Done. All examples passed.")
