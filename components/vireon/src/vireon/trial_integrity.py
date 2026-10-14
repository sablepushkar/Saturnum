from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class TrialEvent:
    event_id: str
    site_id: str
    timestamp: datetime
    event_type: str
    complete: bool = True
    protocol_deviation: bool = False


@dataclass(frozen=True, slots=True)
class SiteIntegrityResult:
    site_id: str
    status: str
    anomaly_score: float
    metrics: dict[str, float]
    flags: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def assess_site(site_id: str, events: list[TrialEvent]) -> SiteIntegrityResult:
    if not site_id.strip():
        raise ValueError("site_id must not be empty")
    if not events:
        raise ValueError("events must be non-empty")

    now = datetime.now(timezone.utc)
    for event in events:
        if not event.event_id.strip() or not event.event_type.strip():
            raise ValueError("trial event_id and event_type must not be empty")
        if event.site_id != site_id:
            raise ValueError("all trial events must belong to the requested site")
        if event.timestamp.tzinfo is None:
            raise ValueError("trial timestamps must be timezone-aware")
        if event.timestamp > now:
            raise ValueError("trial timestamps cannot be in the future")

    missing_rate = sum(not event.complete for event in events) / len(events)
    deviation_rate = sum(event.protocol_deviation for event in events) / len(events)
    duplicate_timestamp_rate = (
        len(events) - len({event.timestamp for event in events})
    ) / len(events)
    duplicate_event_rate = (
        len(events) - len({event.event_id for event in events})
    ) / len(events)
    type_count = len(Counter(event.event_type for event in events))

    anomaly_score = min(
        1.0,
        0.40 * missing_rate
        + 0.30 * deviation_rate
        + 0.15 * duplicate_timestamp_rate
        + 0.15 * duplicate_event_rate,
    )

    flags: list[str] = []
    if missing_rate >= 0.10:
        flags.append("missing_data_pattern")
    if deviation_rate >= 0.10:
        flags.append("protocol_deviation_pattern")
    if duplicate_timestamp_rate >= 0.20:
        flags.append("timestamp_collision_pattern")
    if duplicate_event_rate > 0.0:
        flags.append("duplicate_event_id_pattern")

    return SiteIntegrityResult(
        site_id=site_id,
        status="review" if flags else "monitor",
        anomaly_score=anomaly_score,
        metrics={
            "event_count": float(len(events)),
            "missing_rate": missing_rate,
            "protocol_deviation_rate": deviation_rate,
            "timestamp_collision_rate": duplicate_timestamp_rate,
            "duplicate_event_id_rate": duplicate_event_rate,
            "distinct_event_types": float(type_count),
        },
        flags=tuple(flags),
    )
