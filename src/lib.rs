use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

pub mod constraint;

use constraint::{Constraint as RustConstraint, ConstraintEngine as RustEngine, CheckResult as RustCheckResult};

/// A single range constraint with INT8 saturation semantics.
#[pyclass]
#[derive(Clone)]
struct Constraint {
    inner: RustConstraint,
}

#[pymethods]
impl Constraint {
    #[new]
    fn new(lo: i32, hi: i32, name: &str, severity: u8) -> Self {
        Self {
            inner: RustConstraint::new(lo, hi, name, severity),
        }
    }

    fn check(&self, value: i32) -> CheckResult {
        CheckResult {
            inner: self.inner.check(value),
        }
    }

    #[getter]
    fn lo(&self) -> i32 {
        self.inner.lo
    }

    #[getter]
    fn hi(&self) -> i32 {
        self.inner.hi
    }

    #[getter]
    fn name(&self) -> &str {
        &self.inner.name
    }

    fn __repr__(&self) -> String {
        format!("Constraint(lo={}, hi={}, name='{}', severity={})",
            self.inner.lo, self.inner.hi, self.inner.name, self.inner.severity as u8)
    }
}

/// Result of checking a value against a constraint.
#[pyclass]
#[derive(Clone)]
struct CheckResult {
    inner: RustCheckResult,
}

#[pymethods]
impl CheckResult {
    #[getter]
    fn pass(&self) -> bool {
        self.inner.pass
    }

    #[getter]
    fn error_mask(&self) -> u8 {
        self.inner.error_mask
    }

    #[getter]
    fn severity(&self) -> u8 {
        self.inner.severity
    }

    #[getter]
    fn name(&self) -> &str {
        &self.inner.name
    }

    #[getter]
    fn saturated_value(&self) -> i32 {
        self.inner.saturated_value
    }

    #[getter]
    fn original_value(&self) -> i32 {
        self.inner.original_value
    }

    fn __repr__(&self) -> String {
        let status = if self.inner.pass { "PASS" } else { "FAIL" };
        format!("CheckResult({}, mask=0x{:02x}, sev={}, val={}->{}])",
            status, self.inner.error_mask, self.inner.severity,
            self.inner.original_value, self.inner.saturated_value)
    }

    fn __bool__(&self) -> bool {
        self.inner.pass
    }
}

/// High-performance constraint checking engine.
///
/// Holds multiple constraints and checks values against all of them.
/// Supports batch checking (sequential or parallel via rayon).
#[pyclass]
#[derive(Clone)]
struct ConstraintEngine {
    inner: RustEngine,
}

#[pymethods]
impl ConstraintEngine {
    #[new]
    fn new() -> Self {
        Self {
            inner: RustEngine::new(),
        }
    }

    /// Add a constraint: (lo, hi, name, severity)
    fn add_constraint(&mut self, lo: i32, hi: i32, name: &str, severity: u8) {
        self.inner.add_constraint(lo, hi, name, severity);
    }

    /// Check a single value against all constraints.
    fn check(&self, value: i32) -> Vec<CheckResult> {
        self.inner.check(value)
            .into_iter()
            .map(|r| CheckResult { inner: r })
            .collect()
    }

    /// Check a batch of values against all constraints (sequential).
    fn check_batch(&self, values: Vec<i32>) -> Vec<Vec<CheckResult>> {
        self.inner.check_batch(&values)
            .into_iter()
            .map(|row| row.into_iter().map(|r| CheckResult { inner: r }).collect())
            .collect()
    }

    /// Check a batch of values in parallel using rayon.
    fn check_batch_parallel(&self, values: Vec<i32>) -> Vec<Vec<CheckResult>> {
        self.inner.check_batch_parallel(&values)
            .into_iter()
            .map(|row| row.into_iter().map(|r| CheckResult { inner: r }).collect())
            .collect()
    }

    /// Run a throughput benchmark.
    /// Returns (checks_per_second, total_ms).
    fn benchmark(&self, iterations: usize) -> (f64, f64) {
        self.inner.benchmark(iterations)
    }

    /// Create an engine from a named industry preset.
    ///
    /// Available: battery, automotive, aviation, nuclear, marine, medical
    #[staticmethod]
    fn from_preset(name: &str) -> PyResult<Self> {
        RustEngine::from_preset(name)
            .map(|inner| Self { inner })
            .map_err(|e| PyValueError::new_err(e))
    }

    /// Number of constraints in the engine.
    #[getter]
    fn count(&self) -> usize {
        self.inner.constraints.len()
    }

    fn __repr__(&self) -> String {
        format!("ConstraintEngine({} constraints)", self.inner.constraints.len())
    }
}

/// The FLUX constraint engine — Rust performance, Python ergonomics.
///
/// Core features:
///   - INT8 saturation semantics (zero precision loss)
///   - Batch checking with rayon parallelism
///   - Industry presets (battery, automotive, aviation, nuclear, marine, medical)
///   - DO-178C / ISO 26262 severity classification
///
/// Example:
///     >>> from flux_constraint import ConstraintEngine
///     >>> engine = ConstraintEngine.from_preset("battery")
///     >>> results = engine.check(60)
///     >>> for r in results:
///     ...     print(f"{r.name}: {'PASS' if r.pass else 'FAIL'}")
#[pymodule]
fn _flux(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Constraint>()?;
    m.add_class::<CheckResult>()?;
    m.add_class::<ConstraintEngine>()?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
