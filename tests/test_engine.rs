#[cfg(test)]
mod tests {
    use flux_constraint::constraint::*;

    // ---- Engine edge cases ----

    #[test]
    fn test_empty_engine_check() {
        let engine = ConstraintEngine::new();
        let results = engine.check(42);
        assert!(results.is_empty());
    }

    #[test]
    fn test_empty_engine_batch() {
        let engine = ConstraintEngine::new();
        let results = engine.check_batch(&[1, 2, 3]);
        assert_eq!(results.len(), 3);
        for row in &results {
            assert!(row.is_empty());
        }
    }

    #[test]
    fn test_empty_engine_parallel() {
        let engine = ConstraintEngine::new();
        let results = engine.check_batch_parallel(&[1, 2, 3]);
        assert_eq!(results.len(), 3);
        for row in &results {
            assert!(row.is_empty());
        }
    }

    #[test]
    fn test_default_trait() {
        let engine = ConstraintEngine::default();
        assert!(engine.constraints.is_empty());
    }

    #[test]
    fn test_engine_clone() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "test", 1);
        let cloned = engine.clone();
        assert_eq!(cloned.constraints.len(), 1);
        assert_eq!(cloned.constraints[0].name, "test");

        // Modifying original doesn't affect clone
        engine.add_constraint(-10, 10, "test2", 2);
        assert_eq!(engine.constraints.len(), 2);
        assert_eq!(cloned.constraints.len(), 1);
    }

    #[test]
    fn test_preset_aliases() {
        // Test that alternate preset names work
        let auto1 = ConstraintEngine::from_preset("automotive").unwrap();
        let auto2 = ConstraintEngine::from_preset("automotive_speed").unwrap();
        assert_eq!(auto1.constraints.len(), auto2.constraints.len());

        let av1 = ConstraintEngine::from_preset("aviation").unwrap();
        let av2 = ConstraintEngine::from_preset("aviation_altitude").unwrap();
        assert_eq!(av1.constraints.len(), av2.constraints.len());

        let nuc1 = ConstraintEngine::from_preset("nuclear").unwrap();
        let nuc2 = ConstraintEngine::from_preset("nuclear_temperature").unwrap();
        assert_eq!(nuc1.constraints.len(), nuc2.constraints.len());

        let mar1 = ConstraintEngine::from_preset("marine").unwrap();
        let mar2 = ConstraintEngine::from_preset("marine_depth").unwrap();
        assert_eq!(mar1.constraints.len(), mar2.constraints.len());
    }

    #[test]
    fn test_preset_constraint_count() {
        // All presets have exactly 5 constraints
        for name in &["battery", "automotive", "aviation", "nuclear", "marine", "medical"] {
            let engine = ConstraintEngine::from_preset(name).unwrap();
            assert_eq!(engine.constraints.len(), 5, "Preset '{}' should have 5 constraints", name);
        }
    }

    #[test]
    fn test_engine_multiple_values() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 50, "a", 1);
        engine.add_constraint(25, 75, "b", 2);
        engine.add_constraint(50, 100, "c", 3);

        // Value 37: passes a (0-50) and b (25-75), fails c (50-100)
        let results = engine.check(37);
        assert_eq!(results.len(), 3);
        assert!(results[0].pass);
        assert!(results[1].pass);
        assert!(!results[2].pass);

        // Value 60: fails a, passes b and c
        let results = engine.check(60);
        assert!(!results[0].pass);
        assert!(results[1].pass);
        assert!(results[2].pass);
    }

    #[test]
    fn test_batch_empty_values() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "test", 0);
        let results = engine.check_batch(&[]);
        assert!(results.is_empty());

        let par_results = engine.check_batch_parallel(&[]);
        assert!(par_results.is_empty());
    }

    #[test]
    fn test_batch_single_value() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "test", 0);
        let results = engine.check_batch(&[50]);
        assert_eq!(results.len(), 1);
        assert!(results[0][0].pass);
    }

    #[test]
    fn test_benchmark_empty_engine() {
        // Benchmark on an engine with no constraints should still work
        let engine = ConstraintEngine::new();
        let (rate, ms) = engine.benchmark(5);
        assert!(rate > 0.0);
        assert!(ms > 0.0);
    }

    #[test]
    fn test_constraint_name_preserved() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "velocity", 2);
        engine.add_constraint(-50, 50, "acceleration", 3);

        let results = engine.check(25);
        assert_eq!(results[0].name, "velocity");
        assert_eq!(results[1].name, "acceleration");
    }

    #[test]
    fn test_severity_high_value() {
        // Severity > 3 should be Critical
        let c = Constraint::new(0, 100, "test", 255);
        assert_eq!(c.severity, Severity::Critical);
    }

    #[test]
    fn test_constraint_bounds_saturated() {
        // Constraints with out-of-int8-range bounds should be saturated
        let c = Constraint::new(-200, 200, "test", 0);
        assert_eq!(c.lo, -127);
        assert_eq!(c.hi, 127);
    }

    #[test]
    fn test_inverted_bounds() {
        // lo > hi after saturation: value can never pass
        let c = Constraint::new(100, 0, "inverted", 0);
        // After saturation: lo=100, hi=0 — no value can be in [100, 0]
        let r = c.check(50);
        assert!(!r.pass);
    }

    #[test]
    fn test_single_point_constraint() {
        let c = Constraint::new(42, 42, "exact", 0);
        assert!(c.check(42).pass);
        assert!(!c.check(41).pass);
        assert!(!c.check(43).pass);
    }
}
