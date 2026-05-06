"""Python-side preset helpers for FLUX Constraint Engine.

These provide more detailed preset configurations with metadata
and industry-specific constraint groups.
"""

from typing import Dict, List, Any


PRESET_DETAILS: Dict[str, Dict[str, Any]] = {
    "battery": {
        "standard": "IEC 62619 / UN38.3",
        "domain": "Energy Storage",
        "constraints": {
            "cell_temp": {"lo": 15, "hi": 55, "severity": 3, "unit": "°C",
                          "rationale": "Below 15°C: lithium plating. Above 55°C: thermal runaway risk."},
            "charge_rate": {"lo": 0, "hi": 100, "severity": 2, "unit": "%",
                           "rationale": "C-rate limit for cell longevity."},
            "ambient_temp": {"lo": -40, "hi": 85, "severity": 1, "unit": "°C",
                            "rationale": "Operating environment range."},
            "voltage_mv": {"lo": 2800, "hi": 4200, "severity": 3, "unit": "mV",
                          "rationale": "Over-discharge damages cells. Over-charge: fire."},
            "current_ma": {"lo": 0, "hi": 500, "severity": 2, "unit": "mA",
                          "rationale": "Max continuous discharge current."},
        }
    },
    "automotive": {
        "standard": "ISO 26262 ASIL-D",
        "domain": "Autonomous Driving",
        "constraints": {
            "vehicle_speed": {"lo": 0, "hi": 250, "severity": 2, "unit": "km/h",
                             "rationale": "Speed limit compliance, ACC following distance."},
            "lateral_speed": {"lo": -15, "hi": 15, "severity": 2, "unit": "km/h",
                             "rationale": "Vehicle drift detection."},
            "brake_pressure": {"lo": 0, "hi": 100, "severity": 3, "unit": "bar",
                              "rationale": "Emergency braking trigger threshold."},
            "steering_angle": {"lo": -360, "hi": 360, "severity": 3, "unit": "°",
                              "rationale": "EPS torque limit."},
            "engine_rpm": {"lo": 0, "hi": 5000, "severity": 2, "unit": "rpm",
                          "rationale": "Overspeed protection."},
        }
    },
    "aviation": {
        "standard": "DO-178C DAL A",
        "domain": "eVTOL / Fixed Wing",
        "constraints": {
            "altitude_ft": {"lo": -1000, "hi": 45000, "severity": 3, "unit": "ft",
                           "rationale": "Cabin pressure + terrain clearance."},
            "airspeed_kts": {"lo": 0, "hi": 600, "severity": 3, "unit": "kts",
                            "rationale": "Structural speed limit (Vmo/Mmo)."},
            "pitch_deg": {"lo": -45, "hi": 45, "severity": 3, "unit": "°",
                         "rationale": "Stall / structural load limit."},
            "roll_deg": {"lo": -60, "hi": 60, "severity": 3, "unit": "°",
                        "rationale": "Coordinated flight envelope."},
            "fuel_pct": {"lo": 50, "hi": 110, "severity": 2, "unit": "%",
                        "rationale": "Minimum fuel reserve (50%) + overfill protection."},
        }
    },
    "nuclear": {
        "standard": "NRC 10 CFR 50 / IAEA SSR-2/1",
        "domain": "Nuclear Power",
        "constraints": {
            "reactor_temp_c": {"lo": 280, "hi": 343, "severity": 3, "unit": "°C",
                              "rationale": "Above 343°C: high pressurizer temp trip."},
            "control_rod_pct": {"lo": 0, "hi": 100, "severity": 3, "unit": "%",
                               "rationale": "Rod insertion limit for shutdown margin."},
            "pressure_bar": {"lo": 140, "hi": 170, "severity": 3, "unit": "bar",
                            "rationale": "Primary coolant pressure envelope."},
            "coolant_flow_pct": {"lo": 0, "hi": 100, "severity": 3, "unit": "%",
                                "rationale": "Core cooling flow rate."},
            "neutron_flux_delta": {"lo": -5, "hi": 5, "severity": 3, "unit": "%",
                                  "rationale": "Positive flux rate trip setpoint."},
        }
    },
    "marine": {
        "standard": "IACS / DNV-GL",
        "domain": "Marine / Subsea",
        "constraints": {
            "depth_m": {"lo": 0, "hi": 11000, "severity": 2, "unit": "m",
                       "rationale": "Mariana Trench max depth."},
            "speed_kts": {"lo": 0, "hi": 30, "severity": 2, "unit": "kts",
                         "rationale": "Hull speed limit."},
            "pitch_deg": {"lo": -90, "hi": 90, "severity": 1, "unit": "°",
                         "rationale": "Vessel attitude."},
            "water_temp_c": {"lo": -20, "hi": 50, "severity": 1, "unit": "°C",
                            "rationale": "Equipment operating range."},
            "hull_pressure_pct": {"lo": 0, "hi": 110, "severity": 3, "unit": "%",
                                 "rationale": "Hull stress monitoring."},
        }
    },
    "medical": {
        "standard": "IEC 62304 / IEC 60601",
        "domain": "Medical Devices",
        "constraints": {
            "body_temp_c": {"lo": 36, "hi": 42, "severity": 3, "unit": "°C",
                           "rationale": "Hypothermia <36°C, hyperthermia >42°C."},
            "infusion_ml_h": {"lo": 0, "hi": 1200, "severity": 3, "unit": "mL/h",
                             "rationale": "Bolus volume limit prevents overdose."},
            "heart_rate_bpm": {"lo": 40, "hi": 200, "severity": 3, "unit": "bpm",
                              "rationale": "Bradycardia <40, tachycardia >200."},
            "systolic_bp": {"lo": 0, "hi": 300, "severity": 2, "unit": "mmHg",
                           "rationale": "Hypotension/hypertension thresholds."},
            "spo2_pct": {"lo": 20, "hi": 100, "severity": 3, "unit": "%",
                        "rationale": "Hypoxemia <90%. Below 70%: critical."},
        }
    },
}


def list_presets() -> List[str]:
    """List available preset names."""
    return list(PRESET_DETAILS.keys())


def get_preset_info(name: str) -> Dict[str, Any]:
    """Get detailed information about a preset."""
    if name not in PRESET_DETAILS:
        raise ValueError(f"Unknown preset: {name}. Available: {', '.join(PRESET_DETAILS.keys())}")
    return PRESET_DETAILS[name]


def get_preset_constraints(name: str) -> Dict[str, Dict[str, Any]]:
    """Get just the constraints for a preset."""
    return get_preset_info(name)["constraints"]
