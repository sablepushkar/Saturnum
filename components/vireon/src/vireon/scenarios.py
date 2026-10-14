from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random

from .analytics import distribution_summary
from .core.models import EventType, PharmaEvent
from .signal_engine import detect_signals
from .trial_integrity import TrialEvent, assess_site
from .digital_measures import validate_digital_measure
from .ai_guard import ModelSpec, assess_model


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    name: str
    description: str
    event_count: int
    signal_count: int
    findings: list[dict[str, object]]
    metrics: dict[str, object]
    safety_boundary: str = "Synthetic portfolio demonstration only; no clinical or regulatory decision."

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "event_count": self.event_count,
            "signal_count": self.signal_count,
            "findings": self.findings,
            "metrics": self.metrics,
            "safety_boundary": self.safety_boundary,
        }


SCENARIOS = {
    "normal-trial": "Normal synthetic trial flow",
    "biomarker-signal": "Synthetic biomarker threshold signal",
    "missing-data": "Synthetic digital-measure missingness",
    "site-anomaly": "Synthetic site integrity anomaly",
    "model-drift": "Synthetic model input drift",
    "digital-measure-drift": "Synthetic digital-measure distribution drift",
}


def _events(name: str, seed: int, scenario_time: datetime) -> list[PharmaEvent]:
    rng = Random(seed)
    now = scenario_time
    values = []
    for i in range(12):
        biomarker = 105 + rng.uniform(-8, 8)
        heart_rate = 76 + rng.uniform(-5, 5)
        if name == "biomarker-signal" and i == 9:
            biomarker = 145
        values.append(
            PharmaEvent(
                event_id=f"SCN-{name}-{i:03d}",
                patient_id=f"P-{i%4:02d}",
                site_id="SITE-01",
                event_type=EventType.LAB_RESULT if i % 2 == 0 else EventType.VITAL,
                timestamp=now - timedelta(minutes=i * 10),
                values={"biomarker_x": biomarker, "heart_rate": heart_rate},
                source="synthetic-scenario",
            )
        )
    return values


def run_scenario(name: str, seed: int = 42, evaluated_at: datetime | None = None) -> ScenarioResult:
    key = name.strip().lower()
    if key not in SCENARIOS:
        raise ValueError(f"unknown scenario: {name}; choose one of {sorted(SCENARIOS)}")
    scenario_time = evaluated_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
    if scenario_time.tzinfo is None or scenario_time.utcoffset() is None:
        raise ValueError("evaluated_at must be timezone-aware")
    events = _events(key, seed, scenario_time)
    signals = detect_signals(events, evaluated_at=scenario_time)
    findings: list[dict[str, object]] = [s.as_dict() for s in signals]
    metrics: dict[str, object] = {"seed": seed, "available_scenarios": sorted(SCENARIOS)}

    if key == "missing-data":
        values = [101.0, None, None, 102.0, None, 99.0, None, 100.0]
        result = validate_digital_measure("DM-SYNTH", values, expected_min=80, expected_max=120)
        findings.append(result.as_dict())
    elif key == "site-anomaly":
        now = datetime.now(timezone.utc)
        trial_events = [
            TrialEvent(f"S-{i}", "SITE-01", now - timedelta(minutes=i), "visit", complete=(i != 3), protocol_deviation=(i in {4, 5}))
            for i in range(8)
        ]
        integrity = assess_site("SITE-01", trial_events)
        findings.append(integrity.as_dict())
    elif key == "model-drift":
        reference = [100, 101, 99, 100, 102]
        current = [112, 114, 111, 115, 113]
        guard = assess_model(
            ModelSpec("demo-model", "1.0", "portfolio drift monitoring", "medium", "validated"),
            reference,
            current,
        )
        findings.append({"model_guard": {"status": guard.status, "risk_flags": guard.risk_flags, "metrics": guard.metrics}})
    elif key == "digital-measure-drift":
        metrics["distribution"] = distribution_summary([100, 101, 99, 100, 102], [111, 113, 110, 115, 112])
    else:
        metrics["distribution"] = distribution_summary(
            [e.values["biomarker_x"] for e in events],
            [e.values["heart_rate"] for e in events],
        )

    return ScenarioResult(key, SCENARIOS[key], len(events), len(signals), findings, metrics)
