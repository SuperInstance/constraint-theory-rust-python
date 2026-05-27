"""Python edge-case tests for flux_constraint.

Tests corner cases, pure-Python fallback behavior, and boundary conditions.
Run with: pytest tests/test_edge_cases.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

import pytest
from flux_constraint import (
    Constraint, CheckResult, ConstraintEngine,
    check, battery, automotive, aviation, nuclear, marine, medical,
    PRESETS,
)
from flux_constraint.presets import (
    list_presets, get_preset_info, get_preset_constraints, PRESET_DETAILS,
)


class TestSaturationEdgeCases:
    def test_value_at_int8_max(self):
        c = Constraint(0, 127, "test", 0)
        r = c.check(127)
        assert r.pass_ is True

    def test_value_at_int8_min(self):
        c = Constraint(-127, 0, "test", 0)
        r = c.check(-127)
        assert r.pass_ is True

    def test_saturate_large_positive(self):
        c = Constraint(0, 100, "test", 0)
        r = c.check(99999)
        assert r.saturated_value == 127
        assert r.original_value == 99999

    def test_saturate_large_negative(self):
        c = Constraint(0, 100, "test", 0)
        r = c.check(-99999)
        assert r.saturated_value == -127
        assert r.original_value == -99999

    def test_zero_value(self):
        c = Constraint(-10, 10, "test", 0)
        r = c.check(0)
        assert r.pass_ is True
        assert r.saturated_value == 0

    def test_saturated_value_always_int8(self):
        engine = battery()
        extreme_values = [-(2**31), -1000, -128, 0, 127, 1000, 2**31 - 1]
        for v in extreme_values:
            results = engine.check(v)
            for r in results:
                assert -127 <= r.saturated_value <= 127


class TestConstraintBounds:
    def test_exactly_at_lo(self):
        c = Constraint(10, 50, "test", 0)
        assert c.check(10).pass_ is True

    def test_exactly_at_hi(self):
        c = Constraint(10, 50, "test", 0)
        assert c.check(50).pass_ is True

    def test_one_below_lo(self):
        c = Constraint(10, 50, "test", 0)
        assert c.check(9).pass_ is False

    def test_one_above_hi(self):
        c = Constraint(10, 50, "test", 0)
        assert c.check(51).pass_ is False

    def test_single_point_constraint(self):
        c = Constraint(42, 42, "exact", 0)
        assert c.check(42).pass_ is True
        assert c.check(41).pass_ is False
        assert c.check(43).pass_ is False

    def test_bounds_saturated_on_creation(self):
        """Bounds outside int8 range are saturated."""
        c = Constraint(-200, 200, "wide", 0)
        assert c.lo == -127
        assert c.hi == 127


class TestEmptyEngine:
    def test_empty_check(self):
        engine = ConstraintEngine()
        results = engine.check(42)
        assert results == []

    def test_empty_batch(self):
        engine = ConstraintEngine()
        results = engine.check_batch([1, 2, 3])
        assert len(results) == 3
        assert all(len(r) == 0 for r in results)

    def test_empty_parallel(self):
        engine = ConstraintEngine()
        results = engine.check_batch_parallel([1, 2, 3])
        assert len(results) == 3
        assert all(len(r) == 0 for r in results)

    def test_empty_benchmark(self):
        engine = ConstraintEngine()
        rate, ms = engine.benchmark(5)
        assert rate > 0
        assert ms > 0


class TestBatchOperations:
    def test_batch_empty_values(self):
        engine = ConstraintEngine()
        engine.add_constraint(0, 100, "test", 0)
        results = engine.check_batch([])
        assert results == []

    def test_parallel_empty_values(self):
        engine = ConstraintEngine()
        engine.add_constraint(0, 100, "test", 0)
        results = engine.check_batch_parallel([])
        assert results == []

    def test_batch_single_value(self):
        engine = ConstraintEngine()
        engine.add_constraint(0, 100, "test", 0)
        results = engine.check_batch([50])
        assert len(results) == 1
        assert results[0][0].pass_ is True

    def test_parallel_matches_sequential(self):
        engine = ConstraintEngine()
        engine.add_constraint(-20, 60, "a", 1)
        engine.add_constraint(10, 90, "b", 2)
        engine.add_constraint(0, 100, "c", 3)

        values = list(range(-300, 300, 7))
        seq = engine.check_batch(values)
        par = engine.check_batch_parallel(values)

        for s_row, p_row in zip(seq, par):
            for s, p in zip(s_row, p_row):
                assert s.pass_ == p.pass_
                assert s.saturated_value == p.saturated_value
                assert s.original_value == p.original_value


class TestPresetDetails:
    def test_all_presets_have_details(self):
        for name in list_presets():
            info = get_preset_info(name)
            assert "standard" in info
            assert "domain" in info
            assert "constraints" in info
            assert len(info["constraints"]) > 0

    def test_preset_constraints_structure(self):
        for name in list_presets():
            constraints = get_preset_constraints(name)
            for cname, cdata in constraints.items():
                assert "lo" in cdata, f"Missing 'lo' in {name}/{cname}"
                assert "hi" in cdata, f"Missing 'hi' in {name}/{cname}"
                assert "severity" in cdata, f"Missing 'severity' in {name}/{cname}"

    def test_preset_list_completeness(self):
        presets = list_presets()
        expected = ["battery", "automotive", "aviation", "nuclear", "marine", "medical"]
        for e in expected:
            assert e in presets

    def test_unknown_preset_info_raises(self):
        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset_info("spaceship")

    def test_unknown_preset_constraints_raises(self):
        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset_constraints("does_not_exist")


class TestConvenienceCheck:
    def test_check_pass(self):
        r = check(50, 0, 100)
        assert r.pass_ is True
        assert r.saturated_value == 50

    def test_check_fail(self):
        r = check(200, 0, 100)
        assert r.pass_ is False

    def test_check_boundary(self):
        assert check(0, 0, 100).pass_ is True
        assert check(100, 0, 100).pass_ is True
        assert check(-1, 0, 100).pass_ is False
        assert check(101, 0, 100).pass_ is False

    def test_check_with_name(self):
        r = check(50, 0, 100, name="my_check")
        assert r.name == "my_check"

    def test_check_with_severity(self):
        r = check(50, 0, 100, severity=3)
        assert r.severity == 3


class TestRepr:
    def test_constraint_repr(self):
        c = Constraint(0, 100, "speed", 2)
        r = repr(c)
        assert "speed" in r
        assert "0" in r
        assert "100" in r

    def test_engine_repr(self):
        engine = ConstraintEngine()
        r = repr(engine)
        assert "0 constraints" in r

        engine.add_constraint(0, 100, "test", 0)
        r = repr(engine)
        assert "1 constraints" in r


class TestBoolConversion:
    def test_checkresult_bool_true(self):
        r = check(50, 0, 100)
        assert bool(r) is True

    def test_checkresult_bool_false(self):
        r = check(200, 0, 100)
        assert bool(r) is False


class TestAllFactoryFunctions:
    """Ensure all convenience factory functions return valid engines."""

    @pytest.mark.parametrize("factory,name", [
        (battery, "battery"),
        (automotive, "automotive"),
        (aviation, "aviation"),
        (nuclear, "nuclear"),
        (marine, "marine"),
        (medical, "medical"),
    ])
    def test_factory(self, factory, name):
        engine = factory()
        assert engine.count > 0
        results = engine.check(0)
        assert len(results) == engine.count


class TestVersion:
    def test_version_exists(self):
        from flux_constraint import __version__
        assert isinstance(__version__, str)
        assert len(__version__) > 0
