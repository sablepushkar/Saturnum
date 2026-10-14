from __future__ import annotations
from dataclasses import asdict, dataclass
from math import isfinite

@dataclass(frozen=True, slots=True)
class DigitalMeasureResult:
    measure_id: str
    status: str
    metrics: dict[str, float]
    flags: tuple[str, ...]
    def as_dict(self) -> dict[str, object]:
        return asdict(self)

def validate_digital_measure(measure_id: str, values: list[float | None], *, expected_min: float | None = None, expected_max: float | None = None) -> DigitalMeasureResult:
    if not measure_id.strip():
        raise ValueError("measure_id must not be empty")
    if not values:
        raise ValueError("values must be non-empty")
    if expected_min is not None and not isfinite(expected_min):
        raise ValueError("expected_min must be finite")
    if expected_max is not None and not isfinite(expected_max):
        raise ValueError("expected_max must be finite")
    if expected_min is not None and expected_max is not None and expected_min > expected_max:
        raise ValueError("expected_min must not exceed expected_max")
    observed = [x for x in values if x is not None]
    if any(not isfinite(x) for x in observed):
        raise ValueError("observed values must be finite")
    missingness = 1.0 - len(observed) / len(values)
    flags: list[str] = []
    if not observed:
        flags.append("no_observed_values")
    elif missingness > 0.10:
        flags.append("high_missingness")
    if expected_min is not None and any(x < expected_min for x in observed):
        flags.append("below_expected_range")
    if expected_max is not None and any(x > expected_max for x in observed):
        flags.append("above_expected_range")
    return DigitalMeasureResult(measure_id, "review" if flags else "fit_for_demo", {
        "sample_count": float(len(values)), "observed_count": float(len(observed)),
        "missingness_rate": missingness, "minimum": min(observed) if observed else 0.0,
        "maximum": max(observed) if observed else 0.0,
    }, tuple(flags))
