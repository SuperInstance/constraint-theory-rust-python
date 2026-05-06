#[cfg(test)]
mod tests {
    use flux_constraint::constraint::*;

    #[test]
    fn test_solver_basic() {
        let mut engine = ConstraintEngine::new();
        engine.add_constraint(0, 100, "speed", 2);
        engine.add_constraint(-40, 85, "temp", 3);

        // Value that passes all
        let results = engine.check(50);
        assert!(results.iter().all(|r| r.pass));

        // Value that fails speed but passes temp
        let results = engine.check(-10);
        assert!(!results[0].pass); // speed: -10 not in [0, 100]
        assert!(results[1].pass);  // temp: -10 in [-40, 85]
    }

    #[test]
    fn test_solver_large_batch() {
        let engine = ConstraintEngine::from_preset("battery").unwrap();
        let values: Vec<i32> = (0..10_000).map(|v| (v % 256) - 128).collect();

        let results = engine.check_batch(&values);
        assert_eq!(results.len(), 10_000);

        // Every row should have 5 results (battery has 5 constraints)
        for row in &results {
            assert_eq!(row.len(), 5);
        }
    }

    #[test]
    fn test_solver_parallel_correctness() {
        let engine = ConstraintEngine::from_preset("automotive").unwrap();
        let values: Vec<i32> = (-1000..1000).collect();

        let seq = engine.check_batch(&values);
        let par = engine.check_batch_parallel(&values);

        assert_eq!(seq.len(), par.len());
        for (i, (s, p)) in seq.iter().zip(par.iter()).enumerate() {
            assert_eq!(s.len(), p.len(), "Row {} length mismatch", i);
            for (j, (sr, pr)) in s.iter().zip(p.iter()).enumerate() {
                assert_eq!(sr.pass, pr.pass, "Mismatch at row {} col {}", i, j);
            }
        }
    }

    #[test]
    fn test_solver_cross_preset() {
        // Check that all presets produce valid results for extreme values
        for name in &["battery", "automotive", "aviation", "nuclear", "marine", "medical"] {
            let engine = ConstraintEngine::from_preset(name).unwrap();

            // Extreme values should not panic
            for &v in &[i32::MIN, -128, -1, 0, 1, 127, i32::MAX] {
                let results = engine.check(v);
                assert_eq!(results.len(), engine.constraints.len());
                // At least check that saturated values are in [-127, 127]
                for r in &results {
                    assert!(r.saturated_value >= -127 && r.saturated_value <= 127);
                }
            }
        }
    }
}
