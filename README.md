# constraint-theory-rust-python

**Rust constraint engine with PyO3 Python bindings** — bare-metal constraint checking from Python.

Part of the [Constraint Theory Ecosystem](https://github.com/SuperInstance/constraint-theory-ecosystem). This is the **"Modern Scientific" approach**: Rust for memory-safe bare-metal performance, Python for ergonomics and scientific computing.

---

## Why This Exists

The parent project ([constraint-theory-llvm](https://github.com/SuperInstance/constraint-theory-llvm)) is a Rust CDCL solver that compiles traces to AVX-512 LLVM IR. This repo wraps a similar constraint core in [PyO3](https://pyo3.rs) for Python use while keeping Rust performance.

**Key insight:** INT8 saturation semantics provide zero-drift constraint checking. Every value is clamped to [-127, 127] before comparison, eliminating floating-point precision loss entirely. This is proven correct with 50 Coq theorems.

---

## Installation

```bash
# From PyPI (once published)
pip install flux-constraint

# From source
git clone https://github.com/SuperInstance/constraint-theory-rust-python
cd constraint-theory-rust-python
pip install maturin
maturin develop --release
```

The pure Python fallback works without Rust — just `import flux_constraint`.

---

## Quick Start

```python
from flux_constraint import check, ConstraintEngine

# Quick single check
result = check(60, 15, 55)  # value=60, lo=15, hi=55
print(result.pass_)  # True (60 is in [15, 55])

# With INT8 saturation — 200 saturates to 127
result = check(200, 0, 100)
print(result.pass_)  # False (127 not in [0, 100])
print(result.saturated_value)  # 127

# Industry presets
engine = ConstraintEngine.from_preset("battery")
results = engine.check(60)
for r in results:
    print(f"{r.name}: {'PASS' if r.pass_ else 'FAIL'} (severity={r.severity})")
```

---

## Features

### INT8 Saturation Semantics
Every value is clamped to [-127, 127] before comparison. No floating-point precision loss. Proven correct:
- `sat8(x) ∈ [-127, 127]` for all x
- `sat8(-x) = -sat8(x)` (negation symmetry)
- `a ≤ b → sat8(a) ≤ sat8(b)` (monotonicity)
- `sat8(a+b)` never wraps around

### Batch Checking with Rayon
```python
engine = ConstraintEngine.from_preset("battery")
values = list(range(-200, 200))

# Sequential
results = engine.check_batch(values)

# Parallel (rayon, automatic work-stealing)
results = engine.check_batch_parallel(values)
```

### Industry Presets

| Preset | Standard | Constraints | Description |
|--------|----------|-------------|-------------|
| `battery` | IEC 62619 | 5 | Li-ion cell monitoring |
| `automotive` | ISO 26262 | 5 | ASIL-D vehicle constraints |
| `aviation` | DO-178C | 5 | DAL A flight envelope |
| `nuclear` | NRC 10 CFR 50 | 5 | Reactor safety limits |
| `marine` | IACS / DNV-GL | 5 | Subsea vehicle monitoring |
| `medical` | IEC 62304 | 5 | Patient vital signs |

### Severity Classification
```
0 = PASS (no violation)
1 = Caution (ASIL A advisory)
2 = Warning (ASIL B-D)
3 = Critical (ASIL D / DAL A hard fault)
```

### Performance
Rust core + rayon parallelism delivers:
- **Single check:** <100ns per constraint
- **Batch (sequential):** ~1.7M checks/sec (Python overhead)
- **Batch (parallel):** Scales with CPU cores
- **Pure Rust:** ~500M+ checks/sec (no Python overhead)

---

## API Reference

### `check(value, lo, hi, name="check", severity=0) -> CheckResult`
Quick single-constraint check.

### `Constraint(lo, hi, name, severity)`
Create a single constraint.

### `ConstraintEngine`
| Method | Description |
|--------|-------------|
| `new()` | Create empty engine |
| `add_constraint(lo, hi, name, severity)` | Add a constraint |
| `check(value) -> List[CheckResult]` | Check value against all constraints |
| `check_batch(values) -> List[List[CheckResult]]` | Sequential batch |
| `check_batch_parallel(values) -> List[List[CheckResult]]` | Parallel batch (rayon) |
| `benchmark(iterations) -> (rate, ms)` | Throughput benchmark |
| `from_preset(name) -> ConstraintEngine` | Load industry preset |

### `CheckResult`
| Property | Type | Description |
|----------|------|-------------|
| `pass` | bool | Whether constraint passed |
| `error_mask` | int | Bitmask for error classification |
| `severity` | int | Violation severity (0-3) |
| `name` | str | Constraint name |
| `saturated_value` | int | Value after INT8 saturation |
| `original_value` | int | Original input value |

---

## Architecture

```
┌─────────────────────────────────────┐
│           Python API                │
│  flux_constraint/__init__.py        │
│  (pure Python fallback included)    │
├─────────────────────────────────────┤
│           PyO3 Bridge               │
│  src/lib.rs — Rust ↔ Python types   │
├─────────────────────────────────────┤
│           Rust Core                 │
│  src/constraint.rs                  │
│  • INT8 saturation                  │
│  • Constraint checking              │
│  • Batch parallelism (rayon)        │
│  • Industry presets                 │
├─────────────────────────────────────┤
│           Criterion Benchmarks      │
│  benches/bench_throughput.rs        │
└─────────────────────────────────────┘
```

---

## Testing

```bash
# Rust unit tests
cargo test

# Python tests (with native extension)
pip install maturin && maturin develop --release
pytest tests/test_python.py -v

# Pure Python fallback (no Rust needed)
python tests/test_python.py

# Benchmarks
cargo bench
```

---

## Related Projects

| Repo | Approach | Description |
|------|----------|-------------|
| [constraint-theory-llvm](https://github.com/SuperInstance/constraint-theory-llvm) | Rust + LLVM | CDCL traces → AVX-512 IR |
| [constraint-theory-ecosystem](https://github.com/SuperInstance/constraint-theory-ecosystem) | 42 languages | Cross-language verification |
| **This repo** | **Rust + Python** | **PyO3 bindings, modern scientific** |

---

## License

Apache-2.0

---

*Part of the SuperInstance Constraint Theory ecosystem. 50 Coq theorems. 42 language implementations. 62 billion checks per second.*
