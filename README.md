# constraint-theory-rust-python

Rust constraint engine with PyO3 Python bindings — bare-metal constraint checking with INT8 saturation semantics, rayon-parallel batch evaluation, and 6 industry presets. Accessible from Python with a pure-Python fallback when the native extension isn't compiled.

## What It Does

This crate implements a constraint checking engine where every value is saturated to INT8 range `[-127, 127]` before comparison. This eliminates floating-point drift and ensures deterministic behavior across all implementations. The Rust engine is exposed to Python via PyO3/maturin, with a fallback pure-Python implementation for environments without a compiler.

Key features:
- **INT8 saturation**: All values clamped to `[-127, 127]` with zero precision loss
- **Rayon parallelism**: Batch checks parallelized across cores
- **6 industry presets**: Battery, automotive, aviation, nuclear, marine, medical
- **DO-178C / ISO 26262 severity**: Safety-critical severity classification
- **Pure Python fallback**: Works without Rust compilation

## Installation

### From wheel (recommended)

```bash
pip install flux-constraint
```

### From source (requires Rust toolchain)

```bash
pip install maturin
git clone https://github.com/SuperInstance/constraint-theory-rust-python
cd constraint-theory-rust-python
maturin develop --release
```

Requires Rust ≥ 1.70 and Python ≥ 3.8.

## Quick Start

```python
from flux_constraint import Constraint, ConstraintEngine, check

# Quick single check
result = check(60, 15, 55)
print(result.pass_)           # True or False
print(result.saturated_value) # 60 (in range, not saturated)

# Use an industry preset
engine = ConstraintEngine.from_preset("battery")
results = engine.check(60)
for r in results:
    print(f"{r.name}: {'PASS' if r.pass else 'FAIL'} (sat={r.saturated_value})")

# Batch checking
batch = engine.check_batch([20, 30, 60, 80, 200])
# Parallel version (uses rayon, native extension only)
batch = engine.check_batch_parallel([20, 30, 60, 80, 200])
```

## API

### `Constraint(lo, hi, name, severity)`

A single range constraint. Values are INT8-saturated before checking.

```python
c = Constraint(15, 55, "battery_temp", 3)
result = c.check(60)
# result.pass_, result.error_mask, result.severity
# result.saturated_value, result.original_value
```

### `ConstraintEngine`

Holds multiple constraints and evaluates values against all of them.

| Method | Returns | Description |
|--------|---------|-------------|
| `add_constraint(lo, hi, name, severity)` | — | Add a constraint |
| `check(value)` | `list[CheckResult]` | Check against all constraints |
| `check_batch(values)` | `list[list[CheckResult]]` | Sequential batch |
| `check_batch_parallel(values)` | `list[list[CheckResult]]` | Parallel batch (rayon) |
| `benchmark(iterations)` | `(checks/sec, ms)` | Throughput benchmark |
| `from_preset(name)` | `ConstraintEngine` | Factory from preset name |
| `count` | `int` | Number of constraints |

### `CheckResult`

| Property | Type | Description |
|----------|------|-------------|
| `pass` | `bool` | Whether the saturated value is in bounds |
| `error_mask` | `int` | Bitmask: PASS=0, SAT_MIN=0x01, SAT_MAX=0x02, CONFIDENCE_GAP=0x04, SATURATION=0x08 |
| `severity` | `int` | 0=Pass, 1=Caution, 2=Warning, 3=Critical |
| `saturated_value` | `int` | Value after INT8 saturation |
| `original_value` | `int` | Original input value |
| `name` | `str` | Constraint name |

### Convenience Functions

```python
from flux_constraint import battery, automotive, aviation, nuclear, marine, medical

engine = battery()  # Pre-configured engine
rate, ms = engine.benchmark(500)
```

## Industry Presets

| Preset | Domain | Standard | Constraints |
|--------|--------|----------|-------------|
| `battery` | Li-ion cells | IEC 62619 / UN38.3 | cell_temp, charge_rate, ambient_temp, voltage_mv, current_ma |
| `automotive` | Autonomous driving | ISO 26262 ASIL-D | speed, lateral, brake, steering, rpm |
| `aviation` | eVTOL/Fixed Wing | DO-178C DAL A | altitude, airspeed, pitch, roll, fuel |
| `nuclear` | Reactor monitoring | NRC 10 CFR 50 | reactor_temp, control_rod, pressure, coolant, neutron_flux |
| `marine` | Marine/Subsea | IACS / DNV-GL | depth, speed, pitch, water_temp, hull_pressure |
| `medical` | Medical devices | IEC 62304 | body_temp, infusion, heart_rate, systolic_bp, spo2 |

## INT8 Saturation

```rust
pub fn sat8(val: i32) -> i32 {
    if val < -127 { -127 }
    else if val > 127 { 127 }
    else { val }
}
```

Properties guaranteed by saturation:
- **Monotonicity**: `sat8(a) ≤ sat8(b)` for `a ≤ b`
- **Negation symmetry**: `sat8(-x) == -sat8(x)` for in-range values
- **Determinism**: Same input → same output, always

## Rust API

The underlying Rust types are also usable directly:

```rust
use flux_constraint::{Constraint, ConstraintEngine};

let mut engine = ConstraintEngine::new();
engine.add_constraint(15, 55, "battery_temp", 3);

let results = engine.check(60);
for r in &results {
    println!("{}: pass={} mask=0x{:02x}", r.name, r.pass, r.error_mask);
}

let batch = engine.check_batch_parallel(&[20, 60, 200]);
```

## Building & Testing

```bash
# Rust tests
cargo test

# Python tests (after maturin develop)
pytest tests/

# Benchmarks
cargo bench
```

## Related Repos

- **[flux-check-py](https://github.com/SuperInstance/flux-check-py)** — Pure Python constraint CLI
- **[flux-fracture-c](https://github.com/SuperInstance/flux-fracture-c)** — C99 fracture-coalesce library
- **[constraint-theory-engine-cpp-lua](https://github.com/SuperInstance/constraint-theory-engine-cpp-lua)** — C++ engine with LuaJIT, CDCL solver, AVX-512
- **[polln](https://github.com/SuperInstance/polln)** — Tile-based AI system using constraint theory

## License

Apache-2.0
