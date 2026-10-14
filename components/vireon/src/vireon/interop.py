from __future__ import annotations
from .core.models import PharmaEvent

def to_fhir_observation(event: PharmaEvent) -> dict[str, object]:
    """Create a minimal FHIR R4 Observation boundary payload without fake terminology mappings."""
    components: list[dict[str, object]] = []
    for key, value in event.values.items():
        component: dict[str, object] = {"code": {"text": key}}
        if isinstance(value, bool):
            component["valueBoolean"] = value
        elif isinstance(value, (int, float)):
            component["valueQuantity"] = {"value": value}
        else:
            component["valueString"] = value
        components.append(component)
    payload: dict[str, object] = {
        "resourceType": "Observation",
        "id": event.event_id,
        "status": "final",
        "code": {"text": event.event_type.value},
        "effectiveDateTime": event.timestamp.isoformat(),
        "performer": [{"reference": f"Organization/{event.site_id}"}],
        "component": components,
        "meta": {"tag": [{"system": "https://vireon.local/interop", "code": "synthetic-boundary"}]},
    }
    if event.patient_id:
        payload["subject"] = {"reference": f"Patient/{event.patient_id}"}
    return payload

def to_omop_measurements(event: PharmaEvent) -> dict[str, object]:
    """Return an OMOP-shaped boundary marked non-loadable until terminology mapping exists."""
    rows: list[dict[str, object]] = []
    for key, value in event.values.items():
        rows.append({
            "person_source_value": event.patient_id,
            "measurement_date": event.timestamp.date().isoformat(),
            "measurement_datetime": event.timestamp.isoformat(),
            "measurement_source_value": key,
            "measurement_concept_id": None,
            "value_as_number": value if isinstance(value, (int, float)) and not isinstance(value, bool) else None,
            "value_source_value": str(value),
            "source_event_id": event.event_id,
            "loadable": False,
            "mapping_required": True,
        })
    return {"cdm": "OMOP", "mapping_status": "unmapped_local_keys", "rows": rows}
