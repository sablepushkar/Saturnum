from __future__ import annotations
from datetime import datetime, timezone
from math import isfinite
from .models import PharmaEvent

class EventValidationError(ValueError):
    """Raised when an incoming event violates VIREON domain constraints."""

def validate_event(event: PharmaEvent) -> None:
    if not event.event_id.strip():
        raise EventValidationError("event_id must not be empty")
    if not event.site_id.strip():
        raise EventValidationError("site_id must not be empty")
    if not event.source.strip():
        raise EventValidationError("source must not be empty")
    if event.timestamp.tzinfo is None:
        raise EventValidationError("timestamp must be timezone-aware")
    if event.timestamp > datetime.now(timezone.utc):
        raise EventValidationError("timestamp cannot be in the future")
    for key, value in event.values.items():
        if not isinstance(key, str) or not key.strip():
            raise EventValidationError("event value keys must be non-empty strings")
        if isinstance(value, float) and not isfinite(value):
            raise EventValidationError(f"event value for {key!r} must be finite")
    if event.event_type.value in {"lab_result", "vital"} and not event.values:
        raise EventValidationError(f"{event.event_type.value} events require at least one value")
