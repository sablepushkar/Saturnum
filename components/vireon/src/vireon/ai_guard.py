from __future__ import annotations
from dataclasses import dataclass
from math import isfinite, sqrt

@dataclass(frozen=True, slots=True)
class ModelSpec:
    model_id: str
    version: str
    context_of_use: str
    risk_tier: str
    validation_status: str

@dataclass(frozen=True, slots=True)
class ModelGuardResult:
    model_id: str
    version: str
    status: str
    risk_flags: tuple[str, ...]
    metrics: dict[str, float]

def _mean(values: list[float]) -> float:
    return sum(values) / len(values)

def _stddev(values: list[float]) -> float:
    mean = _mean(values)
    return sqrt(sum((x - mean) ** 2 for x in values) / len(values))

def assess_model(spec: ModelSpec, reference: list[float], current: list[float], *, missing_reference: float = 0.0, missing_current: float = 0.0) -> ModelGuardResult:
    if not spec.model_id.strip() or not spec.version.strip():
        raise ValueError("model_id and version must not be empty")
    if not spec.context_of_use.strip() or not spec.risk_tier.strip():
        raise ValueError("context_of_use and risk_tier must not be empty")
    if not reference or not current:
        raise ValueError("reference and current samples must be non-empty")
    if any(not isfinite(x) for x in reference + current):
        raise ValueError("samples must contain finite numbers")
    if not 0.0 <= missing_reference <= 1.0 or not 0.0 <= missing_current <= 1.0:
        raise ValueError("missingness rates must be between 0 and 1")
    ref_mean, cur_mean = _mean(reference), _mean(current)
    ref_std, cur_std = _stddev(reference), _stddev(current)
    mean_shift = abs(cur_mean - ref_mean) / max(abs(ref_mean), 1.0)
    std_shift = abs(cur_std - ref_std) / max(abs(ref_std), 1.0)
    missing_shift = abs(missing_current - missing_reference)
    flags: list[str] = []
    if mean_shift >= 0.20:
        flags.append("distribution_mean_shift")
    if std_shift >= 0.25:
        flags.append("distribution_variance_shift")
    if missing_shift >= 0.10:
        flags.append("missingness_shift")
    if spec.validation_status.lower() != "validated":
        flags.append("validation_status_not_validated")
    return ModelGuardResult(spec.model_id, spec.version, "review" if flags else "monitor", tuple(flags), {
        "reference_mean": ref_mean, "current_mean": cur_mean, "reference_std": ref_std,
        "current_std": cur_std, "relative_mean_shift": mean_shift,
        "relative_std_shift": std_shift, "missingness_shift": missing_shift,
        "reference_sample_count": float(len(reference)), "current_sample_count": float(len(current)),
    })
