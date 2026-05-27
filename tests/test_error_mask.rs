#[cfg(test)]
mod tests {
    use flux_constraint::constraint::*;

    // ---- Error mask bit tests ----

    #[test]
    fn test_pass_mask_is_zero() {
        let c = Constraint::new(0, 100, "test", 0);
        // Value well within bounds, no saturation
        let r = c.check(50);
        assert!(r.pass);
        assert_eq!(r.error_mask & error_mask::PASS, 0);
        assert_eq!(r.error_mask, 0);
    }

    #[test]
    fn test_saturation_flag_when_out_of_int8() {
        let c = Constraint::new(-50, 50, "test", 0);
        let r = c.check(200);
        assert_ne!(r.error_mask & error_mask::SATURATION, 0);
        assert_eq!(r.saturated_value, 127);
    }

    #[test]
    fn test_saturation_flag_negative() {
        let c = Constraint::new(-50, 50, "test", 0);
        let r = c.check(-200);
        assert_ne!(r.error_mask & error_mask::SATURATION, 0);
        assert_eq!(r.saturated_value, -127);
    }

    #[test]
    fn test_no_saturation_flag_in_range() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(50);
        assert_eq!(r.error_mask & error_mask::SATURATION, 0);
    }

    #[test]
    fn test_sat_min_dot_at_lower_bound() {
        let c = Constraint::new(10, 100, "test", 0);
        let r = c.check(10);
        assert!(r.pass);
        assert_ne!(r.error_mask & error_mask::SAT_MIN_DOT, 0);
    }

    #[test]
    fn test_sat_max_dot_at_upper_bound() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(100);
        assert!(r.pass);
        assert_ne!(r.error_mask & error_mask::SAT_MAX_DOT, 0);
    }

    #[test]
    fn test_confidence_gap_near_boundary() {
        // With range [0, 100], margin is 10. Value 3 should trigger confidence gap.
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(3);
        assert!(r.pass);
        assert_ne!(r.error_mask & error_mask::CONFIDENCE_GAP, 0);
    }

    #[test]
    fn test_confidence_gap_near_upper_boundary() {
        // With range [0, 100], margin is 10. Value 98 should trigger confidence gap.
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(98);
        assert!(r.pass);
        assert_ne!(r.error_mask & error_mask::CONFIDENCE_GAP, 0);
    }

    #[test]
    fn test_no_confidence_gap_midrange() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(50);
        assert!(r.pass);
        assert_eq!(r.error_mask & error_mask::CONFIDENCE_GAP, 0);
    }

    #[test]
    fn test_confidence_gap_not_set_when_saturated() {
        // Saturated values should not trigger confidence gap
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(200);
        assert!(!r.pass);
        assert_eq!(r.error_mask & error_mask::CONFIDENCE_GAP, 0);
    }

    // ---- CheckResult field tests ----

    #[test]
    fn test_check_result_name_propagation() {
        let c = Constraint::new(0, 100, "my_sensor", 2);
        let r = c.check(50);
        assert_eq!(r.name, "my_sensor");
    }

    #[test]
    fn test_check_result_original_value_preserved() {
        let c = Constraint::new(0, 100, "test", 0);
        let r = c.check(999);
        assert_eq!(r.original_value, 999);
        assert_ne!(r.saturated_value, 999); // must be saturated
    }

    #[test]
    fn test_check_result_severity_propagation() {
        for sev in 0..=3 {
            let c = Constraint::new(0, 100, "test", sev);
            let r = c.check(50);
            assert_eq!(r.severity, sev);
        }
    }

    #[test]
    fn test_check_result_saturated_value_in_range() {
        // Saturated value is always in [-127, 127]
        for val in &[i32::MIN, -1000, -128, 0, 127, 1000, i32::MAX] {
            let c = Constraint::new(0, 100, "test", 0);
            let r = c.check(*val);
            assert!(r.saturated_value >= -127 && r.saturated_value <= 127,
                "saturated_value {} out of int8 range for input {}", r.saturated_value, val);
        }
    }

    #[test]
    fn test_multiple_mask_bits() {
        // A value at the lower bound that was saturated from below should have
        // both SAT_MIN_DOT and SATURATION
        let c = Constraint::new(-127, 100, "test", 0);
        let r = c.check(-200); // saturates to -127, which equals lo
        assert!(r.pass);
        assert_ne!(r.error_mask & error_mask::SAT_MIN_DOT, 0);
        assert_ne!(r.error_mask & error_mask::SATURATION, 0);
    }

    #[test]
    fn test_fail_out_of_bounds_no_saturation() {
        // A value within int8 range but outside constraint bounds
        let c = Constraint::new(50, 100, "test", 0);
        let r = c.check(30);
        assert!(!r.pass);
        assert_eq!(r.saturated_value, 30);
        assert_eq!(r.error_mask & error_mask::SATURATION, 0);
    }
}
