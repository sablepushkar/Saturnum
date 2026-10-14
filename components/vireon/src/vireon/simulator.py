from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import Random

from .core.models import EventType, PharmaEvent


def generate_events(
    *,
    count: int = 100,
    seed: int = 42,
    start: datetime | None = None,
) -> list[PharmaEvent]:
    """Generate deterministic synthetic events for development and testing."""
    if count < 0:
        raise ValueError("count must be non-negative")

    start = start or datetime.now(timezone.utc).replace(microsecond=0)
    if start.tzinfo is None:
        raise ValueError("start must be timezone-aware")

    rng = Random(seed)
    events: list[PharmaEvent] = []

    event_types = (
        EventType.LAB_RESULT,
        EventType.VITAL,
        EventType.TREATMENT,
        EventType.ADVERSE_EVENT,
        EventType.TRIAL_OPERATION,
    )

    for index in range(count):
        event_type = rng.choice(event_types)
        timestamp = start + timedelta(minutes=index)

        if event_type is EventType.LAB_RESULT:
            values = {"biomarker_x": round(rng.normalvariate(100, 12), 2)}
            patient_id = f"P{rng.randint(1, 25):04d}"
        elif event_type is EventType.VITAL:
            values = {"heart_rate": round(rng.normalvariate(72, 8), 1)}
            patient_id = f"P{rng.randint(1, 25):04d}"
        elif event_type is EventType.TREATMENT:
            values = {"dose_mg": float(rng.choice((50, 100, 150)))}
            patient_id = f"P{rng.randint(1, 25):04d}"
        elif event_type is EventType.ADVERSE_EVENT:
            values = {"event_present": True, "severity_score": float(rng.randint(1, 3))}
            patient_id = f"P{rng.randint(1, 25):04d}"
        else:
            values = {"operation": rng.choice(("visit", "follow_up", "screening"))}
            patient_id = None

        events.append(
            PharmaEvent(
                event_id=f"E{index + 1:06d}",
                patient_id=patient_id,
                site_id=f"S{rng.randint(1, 5):02d}",
                event_type=event_type,
                timestamp=timestamp,
                values=values,
                source="synthetic-simulator",
            )
        )

    return events
