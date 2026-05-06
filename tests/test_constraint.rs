#[cfg(test)]
mod tests {
    use flux_constraint::constraint::*;

    #[test]
    fn test_sat8_identity() {
        assert_eq!(sat8(50), 50);
        assert_eq!(sat8(-50), -50);
        assert_eq!(sat8(0), 0);
    }

    #[test]
    fn test_sat8_saturates_high() {
        assert_eq!(sat8(200), 127);
        assert_eq!(sat8(128), 127);
        assert_eq!(sat8(127), 127);
    }

    #[test]
    fn test_sat8_saturates_low() {
        assert_eq!(sat8(-200), -127);
        assert_eq!(sat8(-128), -127);
        assert_eq!(sat8(-127), -127);
    }

    #[test]
    fn test_sat8_extremes() {
        assert_eq!(sat8(i32::MAX), 127);
        assert_eq!(sat8(i32::MIN), -127);
    }

    #[test]
    fn test_negation_symmetry() {
        for x in -127..=127 {
            assert_eq!(sat8(-x), -sat8(x), "negation symmetry failed for x={}", x);
        }
    }

    #[test]
    fn test_monotonicity() {
        for a in (-130..130).step_by(7) {
            for b in (a..130).step_by(11) {
                assert!(sat8(a) <= sat8(b));
            }
        }
    }

    #[test]
    fn test_addition_closed() {
        // sat8(a+b) is in [-127, 127] for any a, b
        for a in [-200, -127, -1, 0, 1, 50, 127, 200] {
            for b in [-200, -127, -1, 0, 1, 50, 127, 200] {
                let result = sat8(a + b);
                assert!(result >= -127 && result <= 127,
                    "addition_closed failed: sat8({}+{}) = {}", a, b, result);
            }
        }
    }

    #[test]
    fn test_no_wraparound() {
        // sat8 never wraps — it always clamps
        assert_eq!(sat8(127 + 1), 127);
        assert_eq!(sat8(-127 - 1), -127);
        assert_eq!(sat8(1000 + 1000), 127);
        assert_eq!(sat8(-1000 + (-1000)), -127);
    }

    #[test]
    fn test_constraint_pass() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(50);
        assert!(r.pass);
        assert_eq!(r.saturated_value, 50);
        assert_eq!(r.original_value, 50);
    }

    #[test]
    fn test_constraint_boundary() {
        let c = Constraint::new(0, 100, "test", 0);
        assert!(c.check(0).pass);
        assert!(c.check(100).pass);
        assert!(!c.check(-1).pass);
        assert!(!c.check(101).pass);
    }

    #[test]
    fn test_constraint_saturated_fail() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(200);
        assert!(!r.pass);
        assert_eq!(r.saturated_value, 127); // saturated from 200
        assert_eq!(r.original_value, 200);
        assert_ne!(r.error_mask, error_mask::PASS);
    }

    #[test]
    fn test_engine_check() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "a", 0);
        engine.add_constraint(50, 150, "b", 0);

        let results = engine.check(75);
        assert_eq!(results.len(), 2);
        assert!(results[0].pass); // 75 in [0, 100]
        assert!(results[1].pass); // 75 in [50, 150]
    }

    #[test]
    fn test_engine_batch_sequential() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "test", 0);

        let results = engine.check_batch(&[50, 150, -10]);
        assert!(results[0][0].pass);
        assert!(!results[1][0].pass); // 150 → 127, not in [0,100]
    }

    #[test]
    fn test_engine_batch_parallel_matches_sequential() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "a", 0);
        engine.add_constraint(-50, 50, "b", 1);

        let values: Vec<i32> = (-200..200).collect();
        let seq = engine.check_batch(&values);
        let par = engine.check_batch_parallel(&values);

        for (s, p) in seq.iter().zip(par.iter()) {
            assert_eq!(s.len(), p.len());
            for (sr, pr) in s.iter().zip(p.iter()) {
                assert_eq!(sr.pass, pr.pass);
                assert_eq!(sr.saturated_value, pr.saturated_value);
            }
        }
    }

    #[test]
    fn test_all_presets_valid() {
        for name in &["battery", "automotive", "aviation", "nuclear", "marine", "medical"] {
            let engine = ConstraintEngine::from_preset(name).unwrap();
            assert!(!engine.constraints.is_empty(), "Preset '{}' has no constraints", name);

            // Every preset should handle mid-range values
            let results = engine.check(0);
            assert_eq!(results.len(), engine.constraints.len());
        }
    }

    #[test]
    fn test_unknown_preset_errors() {
        assert!(ConstraintEngine::from_preset("nonexistent").is_err());
        assert!(ConstraintEngine::from_preset("").is_err());
    }

    #[test]
    fn test_benchmark_runs() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "test", 0);
        let (rate, ms) = engine.benchmark(10);
        assert!(rate > 0.0);
        assert!(ms > 0.0);
    }

    #[test]
    fn test_severity_levels() {
        let c0 = Constraint::new(0, 100, "pass", 0);
        let c1 = Constraint::new(0, 100, "caution", 1);
        let c2 = Constraint::new(0, 100, "warning", 2);
        let c3 = Constraint::new(0, 100, "critical", 3);

        assert_eq!(c0.severity, Severity::Pass);
        assert_eq!(c1.severity, Severity::Caution);
        assert_eq!(c2.severity, Severity::Warning);
        assert_eq!(c3.severity, Severity::Critical);
    }
}
