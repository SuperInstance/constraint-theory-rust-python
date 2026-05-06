# Contributing to constraint-theory-rust-python

Thank you for contributing! This project is part of the [Constraint Theory Ecosystem](https://github.com/SuperInstance/constraint-theory-ecosystem).

## Development Setup

```bash
# Clone
git clone https://github.com/SuperInstance/constraint-theory-rust-python
cd constraint-theory-rust-python

# Rust toolchain
rustup update stable

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install maturin pytest

# Build and test
cargo test
maturin develop --release
pytest tests/test_python.py -v
```

## Architecture

- **`src/constraint.rs`** — Core Rust types and logic (no Python dependency)
- **`src/lib.rs`** — PyO3 bridge (Python ↔ Rust)
- **`python/flux_constraint/`** — Python API with pure-Python fallback
- **`tests/`** — Rust and Python tests
- **`benches/`** — Criterion benchmarks

## Adding a New Preset

1. Add the preset to `src/constraint.rs` in `ConstraintEngine::from_preset()`
2. Add matching entry in `python/flux_constraint/__init__.py` (pure Python fallback)
3. Add detailed metadata in `python/flux_constraint/presets.py`
4. Add tests in `tests/test_constraint.rs` and `tests/test_python.py`

## INT8 Saturation Rules

All implementations must match these properties (proven in Coq):

1. `sat8(x) ∈ [-127, 127]` for all x
2. `sat8(-x) = -sat8(x)` for in-range values
3. `a ≤ b → sat8(a) ≤ sat8(b)` (monotonicity)
4. `sat8(a + b)` never wraps around

## Running Benchmarks

```bash
cargo bench
```

Results go to `target/criterion/`. Look for regressions >10%.

## CI

All PRs must pass:
- `cargo check` (no warnings)
- `cargo test` (all Rust tests)
- `pytest tests/test_python.py` (Python tests with native extension)
- Pure Python fallback works without Rust
