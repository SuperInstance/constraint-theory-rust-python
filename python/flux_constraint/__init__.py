"""FLUX Constraint Engine — Rust performance, Python ergonomics.

Usage:
    from flux_constraint import ConstraintEngine, check

    # Quick check
    result = check(60, 15, 55)
    print(result.pass_)  # True

    # Industry preset
    engine = ConstraintEngine.from_preset("battery")
    results = engine.check(60)
    for r in results:
        print(f"{r.name}: {'PASS' if r.pass else 'FAIL'}")

    # Custom engine
    engine = ConstraintEngine()
    engine.add_constraint(15, 55, "battery_temp", 3)
    engine.add_constraint(0, 100, "charge_rate", 2)
    batch_results = engine.check_batch([20, 30, 60, 80])
"""

# Try to import the native Rust module
try:
    from ._flux import Constraint, CheckResult, ConstraintEngine, __version__
except ImportError:
    __version__ = "0.1.0-pure-python"
    # Pure Python fallback (no Rust extension compiled)
    from typing import List, Tuple, Optional
    from dataclasses import dataclass

    INT8_MIN, INT8_MAX = -127, 127

    def _sat8(val: int) -> int:
        return max(INT8_MIN, min(INT8_MAX, val))

    @dataclass
    class CheckResult:
        """Result of checking a value against a constraint."""
        pass_: bool
        error_mask: int
        severity: int
        name: str
        saturated_value: int
        original_value: int

        def __bool__(self):
            return self.pass_

    class Constraint:
        def __init__(self, lo: int, hi: int, name: str = "", severity: int = 0):
            self.lo = _sat8(lo)
            self.hi = _sat8(hi)
            self.name = name
            self.severity = severity

        def check(self, value: int) -> CheckResult:
            sv = _sat8(value)
            passed = sv >= self.lo and sv <= self.hi
            return CheckResult(
                pass_=passed, error_mask=0, severity=self.severity,
                name=self.name, saturated_value=sv, original_value=value
            )

        def __repr__(self):
            return f"Constraint(lo={self.lo}, hi={self.hi}, name='{self.name}', severity={self.severity})"

    class ConstraintEngine:
        def __init__(self):
            self._constraints: List[Constraint] = []

        def add_constraint(self, lo: int, hi: int, name: str, severity: int):
            self._constraints.append(Constraint(lo, hi, name, severity))

        def check(self, value: int) -> List[CheckResult]:
            return [c.check(value) for c in self._constraints]

        def check_batch(self, values: List[int]) -> List[List[CheckResult]]:
            return [self.check(v) for v in values]

        def check_batch_parallel(self, values: List[int]) -> List[List[CheckResult]]:
            return self.check_batch(values)  # Pure Python: no parallelism

        def benchmark(self, iterations: int = 1000) -> Tuple[float, float]:
            import time
            test_vals = [(v % 256) - 128 for v in range(1000)]
            nc = max(len(self._constraints), 1)
            start = time.perf_counter()
            for _ in range(iterations):
                for v in test_vals:
                    self.check(v)
            elapsed = time.perf_counter() - start
            total = iterations * len(test_vals) * nc
            return (total / elapsed, elapsed * 1000)

        @staticmethod
        def from_preset(name: str) -> "ConstraintEngine":
            engine = ConstraintEngine()
            presets = {
                "battery": [(15, 55, "cell_temp", 3), (0, 100, "charge_rate", 2), (-40, 85, "ambient", 1), (2800, 4200, "voltage_mv", 3), (0, 500, "current_ma", 2)],
                "automotive": [(0, 250, "speed", 2), (-15, 15, "lateral", 2), (0, 100, "brake", 3), (-360, 360, "steering", 3), (0, 5000, "rpm", 2)],
                "aviation": [(-1000, 45000, "altitude", 3), (0, 600, "airspeed", 3), (-45, 45, "pitch", 3), (-60, 60, "roll", 3), (50, 110, "fuel", 2)],
                "nuclear": [(280, 343, "reactor_temp", 3), (0, 100, "control_rod", 3), (140, 170, "pressure", 3), (0, 100, "coolant", 3), (-5, 5, "neutron_delta", 3)],
                "marine": [(0, 11000, "depth", 2), (0, 30, "speed", 2), (-90, 90, "pitch", 1), (-20, 50, "water_temp", 1), (0, 110, "hull_pressure", 3)],
                "medical": [(36, 42, "body_temp", 3), (0, 1200, "infusion", 3), (40, 200, "heart_rate", 3), (0, 300, "systolic", 2), (20, 100, "spo2", 3)],
            }
            if name not in presets:
                raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(presets.keys())}")
            for lo, hi, n, s in presets[name]:
                engine.add_constraint(lo, hi, n, s)
            return engine

        @property
        def count(self) -> int:
            return len(self._constraints)

        def __repr__(self):
            return f"ConstraintEngine({len(self._constraints)} constraints)"


# ---- Convenience functions ----

def check(value: int, lo: int, hi: int, name: str = "check", severity: int = 0) -> CheckResult:
    """Quick single constraint check."""
    return Constraint(lo, hi, name, severity).check(value)


def battery() -> ConstraintEngine:
    """Pre-configured battery temperature checker."""
    return ConstraintEngine.from_preset("battery")


def automotive() -> ConstraintEngine:
    """Pre-configured automotive constraint checker."""
    return ConstraintEngine.from_preset("automotive")


def aviation() -> ConstraintEngine:
    """Pre-configured aviation constraint checker."""
    return ConstraintEngine.from_preset("aviation")


def nuclear() -> ConstraintEngine:
    """Pre-configured nuclear constraint checker."""
    return ConstraintEngine.from_preset("nuclear")


def marine() -> ConstraintEngine:
    """Pre-configured marine constraint checker."""
    return ConstraintEngine.from_preset("marine")


def medical() -> ConstraintEngine:
    """Pre-configured medical constraint checker."""
    return ConstraintEngine.from_preset("medical")


PRESETS = {
    "battery": {"lo": 15, "hi": 55, "severity": 3, "description": "Li-ion cell temperature (°C)"},
    "automotive_speed": {"lo": 0, "hi": 250, "severity": 2, "description": "Vehicle speed (km/h)"},
    "aviation_altitude": {"lo": -1000, "hi": 45000, "severity": 3, "description": "Altitude (ft)"},
    "nuclear_temperature": {"lo": 280, "hi": 343, "severity": 3, "description": "Reactor temperature (°C)"},
    "marine_depth": {"lo": 0, "hi": 11000, "severity": 2, "description": "Depth (m)"},
    "medical_body_temp": {"lo": 36, "hi": 42, "severity": 3, "description": "Body temperature (°C)"},
}

__all__ = [
    "Constraint", "CheckResult", "ConstraintEngine",
    "check", "battery", "automotive", "aviation", "nuclear", "marine", "medical",
    "PRESETS", "__version__",
]
