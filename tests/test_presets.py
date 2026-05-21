"""Tests for flux_constraint.presets — preset listing, info, constraints."""

import sys
import os

# Add the python directory to path so we can import before maturin build
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import pytest
from flux_constraint.presets import list_presets, get_preset_info, get_preset_constraints, PRESET_DETAILS


class TestListPresets:
    def test_returns_list(self):
        presets = list_presets()
        assert isinstance(presets, list)
        assert len(presets) > 0

    def test_expected_presets(self):
        presets = list_presets()
        for expected in ["battery", "automotive", "aviation", "nuclear", "marine", "medical"]:
            assert expected in presets


class TestGetPresetInfo:
    def test_battery_info(self):
        info = get_preset_info("battery")
        assert "standard" in info
        assert "domain" in info
        assert "constraints" in info
        assert info["domain"] == "Energy Storage"

    def test_automotive_info(self):
        info = get_preset_info("automotive")
        assert info["domain"] == "Autonomous Driving"

    def test_aviation_info(self):
        info = get_preset_info("aviation")
        assert info["domain"] == "eVTOL / Fixed Wing"

    def test_nuclear_info(self):
        info = get_preset_info("nuclear")
        assert "constraints" in info

    def test_unknown_preset(self):
        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset_info("nonexistent")


class TestGetPresetConstraints:
    def test_battery_constraints(self):
        constraints = get_preset_constraints("battery")
        assert "cell_temp" in constraints
        assert "lo" in constraints["cell_temp"]
        assert "hi" in constraints["cell_temp"]
        assert "severity" in constraints["cell_temp"]

    def test_medical_constraints(self):
        constraints = get_preset_constraints("medical")
        assert "body_temp_c" in constraints
        assert constraints["body_temp_c"]["lo"] == 36
        assert constraints["body_temp_c"]["hi"] == 42


class TestConstraintEnginePresets:
    def test_from_preset(self):
        from flux_constraint import ConstraintEngine
        engine = ConstraintEngine.from_preset("battery")
        assert engine.count > 0

    def test_from_preset_automotive(self):
        from flux_constraint import ConstraintEngine
        engine = ConstraintEngine.from_preset("automotive")
        assert engine.count == 5

    def test_from_preset_unknown(self):
        from flux_constraint import ConstraintEngine
        with pytest.raises(ValueError):
            ConstraintEngine.from_preset("nonexistent")

    def test_check_within_bounds(self):
        from flux_constraint import ConstraintEngine
        engine = ConstraintEngine.from_preset("battery")
        # 30°C is within cell_temp(15,55), charge_rate(0,100), ambient(-40,85), etc.
        # But some constraints like voltage_mv(2800,4200) and current_ma(0,500) will fail for 30
        # So let's just check that the temp constraint passes
        results = engine.check(30)
        temp_result = [r for r in results if r.name == "cell_temp"][0]
        assert temp_result.pass_ is True

    def test_check_out_of_bounds(self):
        from flux_constraint import ConstraintEngine
        engine = ConstraintEngine.from_preset("battery")
        results = engine.check(100)  # outside battery temp range
        assert not all(r.pass_ for r in results)

    def test_batch_check(self):
        from flux_constraint import ConstraintEngine
        engine = ConstraintEngine.from_preset("battery")
        batch = engine.check_batch([20, 30, 40, 50])
        assert len(batch) == 4
        assert all(len(r) == engine.count for r in batch)


class TestConvenienceFunctions:
    def test_check_function(self):
        from flux_constraint import check
        result = check(30, 15, 55)
        assert result.pass_ is True

    def test_check_out_of_range(self):
        from flux_constraint import check
        result = check(100, 15, 55)
        assert result.pass_ is False

    def test_battery_factory(self):
        from flux_constraint import battery
        engine = battery()
        assert engine.count > 0

    def test_aviation_factory(self):
        from flux_constraint import aviation
        engine = aviation()
        assert engine.count > 0

    def test_nuclear_factory(self):
        from flux_constraint import nuclear
        engine = nuclear()
        assert engine.count > 0

    def test_marine_factory(self):
        from flux_constraint import marine
        engine = marine()
        assert engine.count > 0

    def test_medical_factory(self):
        from flux_constraint import medical
        engine = medical()
        assert engine.count > 0


class TestConstraint:
    def test_repr(self):
        from flux_constraint import Constraint
        c = Constraint(0, 100, "test", 2)
        r = repr(c)
        assert "test" in r

    def test_boundary_values(self):
        from flux_constraint import Constraint
        c = Constraint(0, 100, "test", 1)
        assert c.check(0).pass_ is True
        assert c.check(100).pass_ is True
        assert c.check(-1).pass_ is False
        assert c.check(101).pass_ is False


class TestCheckResult:
    def test_bool_conversion(self):
        from flux_constraint import check
        result_pass = check(50, 0, 100)
        assert bool(result_pass) is True
        result_fail = check(200, 0, 100)
        assert bool(result_fail) is False
