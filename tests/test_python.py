"""Python integration tests for flux_constraint.

Run with: pytest tests/test_python.py -v
Or without pytest: python tests/test_python.py
"""
import sys
import os

# Add the python directory to path so we can import before maturin build
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from flux_constraint import (
    Constraint, CheckResult, ConstraintEngine,
    check, battery, automotive, aviation, nuclear, marine, medical,
    PRESETS,
)


def test_quick_check():
    """Test the convenience check() function."""
    r = check(50, 0, 100)
    assert r.pass_ is True  # native uses pass_

    r = check(200, 0, 100)
    assert r.pass_ is False


def test_constraint_basic():
    """Test Constraint creation and checking."""
    c = Constraint(15, 55, "battery_temp", 3)
    assert c.lo == 15
    assert c.hi == 55

    r = c.check(30)
    assert r.pass_ is True
    assert r.saturated_value == 30


def test_constraint_saturates():
    """Test INT8 saturation."""
    c = Constraint(0, 100, "test", 0)
    r = c.check(200)
    # 200 saturates to 127
    assert r.saturated_value == 127
    assert r.original_value == 200


def test_engine_basic():
    """Test ConstraintEngine."""
    engine = ConstraintEngine()
    engine.add_constraint(15, 55, "temp", 3)
    engine.add_constraint(0, 100, "charge", 2)
    assert engine.count == 2

    results = engine.check(30)
    assert len(results) == 2


def test_engine_batch():
    """Test batch checking."""
    engine = ConstraintEngine()
    engine.add_constraint(0, 100, "test", 0)

    results = engine.check_batch([50, 75, 100])
    assert len(results) == 3
    for row in results:
        assert len(row) == 1


def test_engine_parallel():
    """Test parallel batch checking matches sequential."""
    engine = ConstraintEngine()
    engine.add_constraint(0, 100, "a", 0)
    engine.add_constraint(-50, 50, "b", 1)

    values = list(range(-200, 200))
    seq = engine.check_batch(values)
    par = engine.check_batch_parallel(values)

    assert len(seq) == len(par)
    for s_row, p_row in zip(seq, par):
        assert len(s_row) == len(p_row)
        for s, p in zip(s_row, p_row):
            s_pass = s.pass_
            p_pass = p.pass_
            assert s_pass == p_pass


def test_all_presets():
    """Test all preset factories."""
    for factory, name in [(battery, "battery"), (automotive, "automotive"),
                          (aviation, "aviation"), (nuclear, "nuclear"),
                          (marine, "marine"), (medical, "medical")]:
        engine = factory()
        assert engine.count > 0, f"Preset {name} has no constraints"

        # Check that it produces results
        results = engine.check(0)
        assert len(results) == engine.count


def test_from_preset():
    """Test ConstraintEngine.from_preset()."""
    for name in ["battery", "automotive", "aviation", "nuclear", "marine", "medical"]:
        engine = ConstraintEngine.from_preset(name)
        assert engine.count > 0

    # Unknown preset should error
    try:
        ConstraintEngine.from_preset("nonexistent")
        assert False, "Should have raised"
    except (ValueError, Exception):
        pass


def test_benchmark():
    """Test benchmark runs without error."""
    engine = ConstraintEngine.from_preset("battery")
    rate, ms = engine.benchmark(10)
    assert rate > 0
    assert ms > 0


def test_presets_dict():
    """Test PRESETS metadata."""
    assert len(PRESETS) >= 6
    assert "battery" in PRESETS
    assert "lo" in PRESETS["battery"]
    assert "hi" in PRESETS["battery"]


def test_extreme_values():
    """Test that extreme values don't crash."""
    engine = ConstraintEngine.from_preset("battery")
    for v in [-2**31, -1000, -128, 0, 127, 1000, 2**31 - 1]:
        results = engine.check(v)
        for r in results:
            assert -127 <= r.saturated_value <= 127


if __name__ == "__main__":
    # Run without pytest
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
