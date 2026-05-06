/// INT8 saturation — the core of zero-drift constraint checking.
/// Every language implementation must match this exactly.
#[inline(always)]
pub fn sat8(val: i32) -> i32 {
    const INT8_MIN: i32 = -127;
    const INT8_MAX: i32 = 127;
    if val < INT8_MIN {
        INT8_MIN
    } else if val > INT8_MAX {
        INT8_MAX
    } else {
        val
    }
}

/// Error mask bits for constraint result classification.
pub mod error_mask {
    pub const PASS: u8 = 0x00;
    pub const SAT_MIN_DOT: u8 = 0x01; // Value hit saturated lower bound
    pub const SAT_MAX_DOT: u8 = 0x02; // Value hit saturated upper bound
    pub const CONFIDENCE_GAP: u8 = 0x04; // Within bounds but near edge
    pub const SATURATION: u8 = 0x08; // Value was saturated from out-of-range
}

/// Severity levels matching DO-178C / ISO 26262 classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Severity {
    Pass = 0,
    Caution = 1,  // ASIL A / DAL D advisory
    Warning = 2,  // ASIL B-D / DAL B-C
    Critical = 3, // ASIL D / DAL A hard fault
}

/// A single range constraint with INT8 saturation semantics.
#[derive(Debug, Clone)]
pub struct Constraint {
    pub lo: i32,
    pub hi: i32,
    pub name: String,
    pub severity: Severity,
}

impl Constraint {
    pub fn new(lo: i32, hi: i32, name: &str, severity: u8) -> Self {
        let sev = match severity {
            0 => Severity::Pass,
            1 => Severity::Caution,
            2 => Severity::Warning,
            _ => Severity::Critical,
        };
        Self {
            lo: sat8(lo),
            hi: sat8(hi),
            name: name.to_string(),
            severity: sev,
        }
    }

    /// Check a value against this constraint.
    /// Returns a CheckResult with pass/fail, error mask, and severity.
    pub fn check(&self, value: i32) -> CheckResult {
        let sv = sat8(value);
        let was_saturated = sv != value;
        let passed = sv >= self.lo && sv <= self.hi;

        let mut mask = error_mask::PASS;
        if was_saturated {
            mask |= error_mask::SATURATION;
        }
        if sv == self.lo {
            mask |= error_mask::SAT_MIN_DOT;
        }
        if sv == self.hi {
            mask |= error_mask::SAT_MAX_DOT;
        }
        if passed && !was_saturated {
            // Check if near boundary (within 10% of range)
            let range = self.hi - self.lo;
            if range > 0 {
                let margin = range / 10;
                if sv - self.lo <= margin || self.hi - sv <= margin {
                    mask |= error_mask::CONFIDENCE_GAP;
                }
            }
        }

        CheckResult {
            pass: passed,
            error_mask: mask,
            severity: self.severity as u8,
            name: self.name.clone(),
            saturated_value: sv,
            original_value: value,
        }
    }
}

/// Result of checking a value against a constraint.
#[derive(Debug, Clone)]
pub struct CheckResult {
    pub pass: bool,
    pub error_mask: u8,
    pub severity: u8,
    pub name: String,
    pub saturated_value: i32,
    pub original_value: i32,
}

/// A constraint engine that holds multiple constraints and checks values against all of them.
#[derive(Debug, Clone)]
pub struct ConstraintEngine {
    pub constraints: Vec<Constraint>,
}

impl ConstraintEngine {
    pub fn new() -> Self {
        Self {
            constraints: Vec::new(),
        }
    }

    /// Add a constraint to the engine.
    pub fn add_constraint(&mut self, lo: i32, hi: i32, name: &str, severity: u8) {
        self.constraints.push(Constraint::new(lo, hi, name, severity));
    }

    /// Check a single value against all constraints.
    pub fn check(&self, value: i32) -> Vec<CheckResult> {
        self.constraints.iter().map(|c| c.check(value)).collect()
    }

    /// Check a batch of values against all constraints (sequential).
    pub fn check_batch(&self, values: &[i32]) -> Vec<Vec<CheckResult>> {
        values.iter().map(|v| self.check(*v)).collect()
    }

    /// Check a batch of values in parallel using rayon.
    pub fn check_batch_parallel(&self, values: &[i32]) -> Vec<Vec<CheckResult>> {
        use rayon::prelude::*;
        values
            .par_iter()
            .map(|v| self.check(*v))
            .collect()
    }

    /// Run a throughput benchmark.
    /// Returns (checks_per_second, total_ms).
    pub fn benchmark(&self, iterations: usize) -> (f64, f64) {
        let test_values: Vec<i32> = (0..1000).map(|v| (v % 256) - 128).collect();
        let n_constraints = self.constraints.len().max(1);

        let start = std::time::Instant::now();
        for _ in 0..iterations {
            for &v in &test_values {
                std::hint::black_box(self.check(v));
            }
        }
        let elapsed = start.elapsed().as_secs_f64();
        let total_checks = iterations * test_values.len() * n_constraints;
        let checks_per_sec = total_checks as f64 / elapsed;
        let ms = elapsed * 1000.0;

        (checks_per_sec, ms)
    }

    /// Create an engine from a named industry preset.
    pub fn from_preset(name: &str) -> Result<Self, String> {
        let mut engine = Self::new();
        match name {
            "battery" => {
                engine.add_constraint(15, 55, "cell_temp", 3);
                engine.add_constraint(0, 100, "charge_rate", 2);
                engine.add_constraint(-40, 85, "ambient_temp", 1);
                engine.add_constraint(2800, 4200, "voltage_mv", 3);
                engine.add_constraint(0, 500, "current_ma", 2);
            }
            "automotive" | "automotive_speed" => {
                engine.add_constraint(0, 250, "vehicle_speed", 2);
                engine.add_constraint(-15, 15, "lateral_speed", 2);
                engine.add_constraint(0, 100, "brake_pressure", 3);
                engine.add_constraint(-360, 360, "steering_angle", 3);
                engine.add_constraint(0, 5000, "rpm", 2);
            }
            "aviation" | "aviation_altitude" => {
                engine.add_constraint(-1000, 45000, "altitude_ft", 3);
                engine.add_constraint(0, 600, "airspeed_kts", 3);
                engine.add_constraint(-45, 45, "pitch_deg", 3);
                engine.add_constraint(-60, 60, "roll_deg", 3);
                engine.add_constraint(50, 110, "fuel_pct", 2);
            }
            "nuclear" | "nuclear_temperature" => {
                engine.add_constraint(280, 343, "reactor_temp_c", 3);
                engine.add_constraint(0, 100, "control_rod_pct", 3);
                engine.add_constraint(140, 170, "pressure_bar", 3);
                engine.add_constraint(0, 100, "coolant_flow_pct", 3);
                engine.add_constraint(-5, 5, "neutron_flux_delta", 3);
            }
            "marine" | "marine_depth" => {
                engine.add_constraint(0, 11000, "depth_m", 2);
                engine.add_constraint(0, 30, "speed_kts", 2);
                engine.add_constraint(-90, 90, "pitch_deg", 1);
                engine.add_constraint(-20, 50, "water_temp_c", 1);
                engine.add_constraint(0, 110, "hull_pressure_pct", 3);
            }
            "medical" => {
                engine.add_constraint(36, 42, "body_temp_c", 3);
                engine.add_constraint(0, 1200, "infusion_ml_h", 3);
                engine.add_constraint(40, 200, "heart_rate_bpm", 3);
                engine.add_constraint(0, 300, "systolic_bp", 2);
                engine.add_constraint(20, 100, "spo2_pct", 3);
            }
            _ => return Err(format!("Unknown preset: '{}'. Available: battery, automotive, aviation, nuclear, marine, medical", name)),
        }
        Ok(engine)
    }
}

impl Default for ConstraintEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sat8_in_range() {
        assert_eq!(sat8(50), 50);
        assert_eq!(sat8(-50), -50);
        assert_eq!(sat8(0), 0);
    }

    #[test]
    fn test_sat8_saturates() {
        assert_eq!(sat8(200), 127);
        assert_eq!(sat8(-200), -127);
        assert_eq!(sat8(i32::MAX), 127);
        assert_eq!(sat8(i32::MIN), -127);
    }

    #[test]
    fn test_sat8_boundary() {
        assert_eq!(sat8(127), 127);
        assert_eq!(sat8(-127), -127);
        assert_eq!(sat8(128), 127);
        assert_eq!(sat8(-128), -127);
    }

    #[test]
    fn test_constraint_pass() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(50);
        assert!(r.pass);
        assert_eq!(r.saturated_value, 50);
    }

    #[test]
    fn test_constraint_fail() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(150);
        assert!(!r.pass);
        assert_eq!(r.saturated_value, 127); // saturated to 127
        assert_ne!(r.error_mask, error_mask::PASS);
    }

    #[test]
    fn test_engine_batch() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "test", 0);
        let results = engine.check_batch(&[50, 150, -10]);
        assert!(results[0][0].pass);   // 50 in [0,100]
        assert!(!results[1][0].pass);  // 150→127 not in [0,100] (saturated)
        assert!(!results[2][0].pass);  // -10 in [0,100]? yes actually
    }

    #[test]
    fn test_all_presets() {
        for name in &["battery", "automotive", "aviation", "nuclear", "marine", "medical"] {
            let engine = ConstraintEngine::from_preset(name).unwrap();
            assert!(!engine.constraints.is_empty());
        }
    }

    #[test]
    fn test_unknown_preset() {
        assert!(ConstraintEngine::from_preset("nonexistent").is_err());
    }

    #[test]
    fn test_negation_symmetry() {
        // sat8(-x) == -sat8(x) for in-range values
        for x in -127..=127 {
            assert_eq!(sat8(-x), -sat8(x), "Failed for x={}", x);
        }
    }

    #[test]
    fn test_monotonicity() {
        // sat8(a) <= sat8(b) for a <= b
        for a in (-130..130).step_by(7) {
            for b in (a..130).step_by(11) {
                assert!(sat8(a) <= sat8(b), "Monotonicity failed: sat8({})={} > sat8({})={}", a, sat8(a), b, sat8(b));
            }
        }
    }
}
