# constraint-theory-rust-python

[![PyPI version](https://img.shields.io/pypi/v/cocapn)](https://pypi.org/project/cocapn/) [![crates.io](https://img.shields.io/crates/v/placeholder)](https://crates.io/crates/placeholder) [![SuperInstance](https://img.shields.io/badge/SuperInstance-Ecosystem-blue)](https://github.com/SuperInstance)



Rust constraint engine with Python bindings (PyO3) — INT8 saturation semantics, batch constraint checking, and zero-copy Python interop.

## What This Gives You

- **INT8 saturation arithmetic** — constraint checking in 8-bit integer space with defined overflow semantics
- **PyO3 bindings** — call the Rust engine from Python with zero-copy data transfer
- **Batch processing** — evaluate thousands of constraint sets in microseconds
- **Memory-safe** — Rust's ownership model guarantees no buffer overflows or use-after-free
- **Pythonic API** — feels like a native Python library

## Quick Start

### Python

```python
import constraint_engine_rs

# Create engine with INT8 saturation mode
engine = constraint_engine_rs.Engine(mode="int8_saturating")

# Batch snap points to Eisenstein lattice
points = [(0.5, 0.3), (1.2, 0.8), (2.1, 1.5)]
results = engine.batch_snap(points, lattice="eisenstein_a2")

for pt, snap in zip(points, results):
    print(f"{pt} → ({snap.a}, {snap.b}), error={snap.error:.4f}")
```

### Rust

```rust
use constraint_engine::{Engine, LatticeType, SaturationMode};

let mut engine = Engine::new(SaturationMode::Int8);
let results = engine.batch_snap(&points, LatticeType::EisensteinA2);

for r in &results {
    println!("({}, {}) error={:.4}", r.a, r.b, r.error);
}
```

## API Reference

| Class / Function | Description |
|---|---|
| `Engine(mode)` | Create engine (`"int8_saturating"`, `"float64"`) |
| `engine.batch_snap(points, lattice)` | Snap points to lattice |
| `engine.check_funnel(points, decay, tolerance)` | Apply deadband funnel |
| `engine.verify_holonomy(tiles, mod_val)` | Check cycle consistency |
| `engine.check_laman(n, edges)` | Verify Laman rigidity |

## Building

```bash
# Rust library
cargo build --release

# Python wheel
maturin develop --release
```

### Dependencies

- Rust 1.70+
- Python ≥ 3.10 (for bindings)
- PyO3 + maturin (for Python wheel)

## How It Fits

The **Rust+Python engine** in the constraint theory ecosystem:

- [constraint-theory-core](https://github.com/SuperInstance/constraint-theory-core) — Python+Rust unified library (theory)
- [constraint-theory-engine-cpp-lua](https://github.com/SuperInstance/constraint-theory-engine-cpp-lua) — C++ alternative engine
- [constraint-substrate](https://github.com/SuperInstance/constraint-substrate) — cross-language primitive verification

## Testing

```bash
# Rust tests
cargo test

# Python tests
pytest tests/
```

## Installation

```bash
pip install constraint-engine-rs
```

## License

MIT

## Documentation

📚 [OpenConstruct Docs](https://github.com/SuperInstance/openconstruct-docs)
