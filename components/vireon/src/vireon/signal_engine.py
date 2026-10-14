from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Iterable

from .core.models import PharmaEvent, Signal
from .core.validation import validate_event

DETECTOR_VERSION = "threshold-rules/0.2"


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def _finite_threshold(value: object, name: str) -> float:
    try:
        number = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def detect_signals(
    events: Iterable[PharmaEvent],
    *,
    biomarker_x_threshold: float = 130.0,
    heart_rate_threshold: float = 120.0,
    evaluated_at: datetime | None = None,
) -> list[Signal]:
    """Create review signals; pass ``evaluated_at`` to reproduce a prior run.

    Thresholds and inputs are deterministic. The default timestamp records when
    this invocation ran; a supplied timezone-aware timestamp makes the complete
    Signal objects repeatable for tests, comparisons, and historical replays.
    """
    biomarker_x_threshold = _finite_threshold(biomarker_x_threshold, "biomarker_x_threshold")
    heart_rate_threshold = _finite_threshold(heart_rate_threshold, "heart_rate_threshold")
    if evaluated_at is None:
        evaluated_at = datetime.now(timezone.utc)
    elif evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise ValueError("evaluated_at must be timezone-aware")
    signals: list[Signal] = []
    for event in events:
        validate_event(event)
        biomarker = _number(event.values.get("biomarker_x"))
        heart_rate = _number(event.values.get("heart_rate"))

        if biomarker is not None and biomarker >= biomarker_x_threshold:
            signals.append(
                Signal(
                    signal_id=f"SIG-{event.event_id}",
                    event_id=event.event_id,
                    signal_type="biomarker_x_high",
                    severity="review",
                    reason=f"biomarker_x={biomarker:g} >= threshold={biomarker_x_threshold:g}",
                    detector_version=DETECTOR_VERSION,
                    detected_at=evaluated_at,
                )
            )

        if heart_rate is not None and heart_rate >= heart_rate_threshold:
            signals.append(
                Signal(
                    signal_id=f"SIG-{event.event_id}-HEART_RATE",
                    event_id=event.event_id,
                    signal_type="heart_rate_high",
                    severity="review",
                    reason=f"heart_rate={heart_rate:g} >= threshold={heart_rate_threshold:g}",
                    detector_version=DETECTOR_VERSION,
                    detected_at=evaluated_at,
                )
            )

    return signals
