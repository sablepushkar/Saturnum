from __future__ import annotations

from math import isfinite, sqrt
from statistics import mean, pstdev
from typing import Sequence


def summarize(values: Sequence[float | None]) -> dict[str, float | int | None]:
    observed = [float(v) for v in values if v is not None and isfinite(float(v))]
    missing = len(values) - len(observed)
    if not observed:
        return {"count": len(values), "observed": 0, "missing": missing, "missing_rate": 1.0, "mean": None, "std": None}
    return {
        "count": len(values),
        "observed": len(observed),
        "missing": missing,
        "missing_rate": missing / len(values),
        "mean": mean(observed),
        "std": pstdev(observed) if len(observed) > 1 else 0.0,
    }


def z_score(value: float, baseline: Sequence[float]) -> float:
    if not baseline:
        raise ValueError("baseline must be non-empty")
    avg = mean(baseline)
    sd = pstdev(baseline)
    if sd == 0:
        return 0.0 if value == avg else float("inf")
    return (value - avg) / sd


def mean_shift(reference: Sequence[float], current: Sequence[float]) -> float:
    if not reference or not current:
        raise ValueError("reference and current must be non-empty")
    return mean(current) - mean(reference)


def distribution_summary(reference: Sequence[float], current: Sequence[float]) -> dict[str, float]:
    shift = mean_shift(reference, current)
    ref_sd = pstdev(reference) if len(reference) > 1 else 0.0
    return {
        "reference_mean": mean(reference),
        "current_mean": mean(current),
        "mean_shift": shift,
        "reference_std": ref_sd,
        "current_std": pstdev(current) if len(current) > 1 else 0.0,
        "standardized_shift": shift / ref_sd if ref_sd else 0.0,
    }
