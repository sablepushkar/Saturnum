from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import __version__
from .ai_guard import ModelSpec, assess_model
from .config import VireonConfig, load_config
from .scenarios import SCENARIOS, run_scenario
from .core.models import EventType, EvidenceLink, PharmaEvent
from .core.validation import EventValidationError, validate_event
from .digital_measures import validate_digital_measure
from .evidence_graph import EvidenceGraph
from .evidence_manifest import build_manifest
from .registry import Registry
from .interop import to_fhir_observation, to_omop_measurements
from .lifecycle import simulate_lifecycle
from .signal_engine import detect_signals
from .storage.sqlite import EventStore
from .trial_integrity import TrialEvent, assess_site


class EventRequest(BaseModel):
    event_id: str = Field(min_length=1)
    patient_id: str | None = None
    site_id: str = Field(min_length=1)
    event_type: EventType
    timestamp: datetime
    values: dict[str, float | str | bool]
    source: str = Field(min_length=1)


class ModelGuardRequest(BaseModel):
    model_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    context_of_use: str = Field(min_length=1)
    risk_tier: str = Field(min_length=1)
    validation_status: str = Field(min_length=1)
    reference: list[float] = Field(min_length=1)
    current: list[float] = Field(min_length=1)
    missing_reference: float = 0.0
    missing_current: float = 0.0


class DigitalMeasureRequest(BaseModel):
    measure_id: str = Field(min_length=1)
    values: list[float | None] = Field(min_length=1)
    expected_min: float | None = None
    expected_max: float | None = None


class TrialEventRequest(BaseModel):
    event_id: str = Field(min_length=1)
    site_id: str = Field(min_length=1)
    timestamp: datetime
    event_type: str = Field(min_length=1)
    complete: bool = True
    protocol_deviation: bool = False


def _to_domain(request: EventRequest) -> PharmaEvent:
    event = PharmaEvent(
        event_id=request.event_id,
        patient_id=request.patient_id,
        site_id=request.site_id,
        event_type=request.event_type,
        timestamp=request.timestamp,
        values=request.values,
        source=request.source,
    )

    try:
        validate_event(event)
    except EventValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return event


def create_app(database_path: str | Path | None = None, config: VireonConfig | None = None) -> FastAPI:
    config = config or load_config()
    database_path = database_path or config.database_path
    app = FastAPI(
        title="VIREON",
        version=__version__,
        description=(
            "Synthetic-data-first pharmaceutical lifecycle intelligence prototype."
        ),
    )
    store = EventStore(database_path)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "vireon",
            "version": __version__,
        }

    @app.post("/v1/events", status_code=status.HTTP_201_CREATED)
    def create_event(request: EventRequest) -> dict[str, Any]:
        event = _to_domain(request)
        store.save(event)
        return event.as_dict()

    @app.get("/v1/events")
    def list_events(limit: int = Query(default=min(100, config.max_query_limit), ge=1, le=config.max_query_limit)) -> dict[str, Any]:
        events = store.list_events(limit)
        return {
            "count": len(events),
            "events": [event.as_dict() for event in events],
        }

    @app.get("/v1/events/{event_id}")
    def get_event(event_id: str) -> dict[str, Any]:
        event = store.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="event not found")
        return event.as_dict()

    @app.post("/v1/signals/detect")
    def detect_current_signals(
        limit: int = Query(default=config.max_query_limit, ge=1, le=config.max_query_limit),
    ) -> dict[str, Any]:
        events = store.list_events(limit)
        signals = detect_signals(
            events,
            biomarker_x_threshold=config.biomarker_x_threshold,
            heart_rate_threshold=config.heart_rate_threshold,
        )

        for signal in signals:
            store.save_signal(signal)
            store.save_evidence(
                EvidenceLink(
                    evidence_id=f"EVD-{signal.signal_id}",
                    signal_id=signal.signal_id,
                    event_id=signal.event_id,
                    relationship="detected_from",
                    detector_version=signal.detector_version,
                    created_at=signal.detected_at,
                )
            )

        return {
            "event_count": len(events),
            "signal_count": len(signals),
            "signals": [signal.as_dict() for signal in signals],
        }

    @app.get("/v1/signals")
    def list_signals(limit: int = Query(default=min(100, config.max_query_limit), ge=1, le=config.max_query_limit)) -> dict[str, Any]:
        signals = store.list_signals(limit)
        return {
            "count": len(signals),
            "signals": [signal.as_dict() for signal in signals],
        }

    @app.get("/v1/signals/{signal_id}")
    def get_signal(signal_id: str) -> dict[str, Any]:
        signal = store.get_signal(signal_id)
        if signal is None:
            raise HTTPException(status_code=404, detail="signal not found")
        return signal.as_dict()

    @app.get("/v1/signals/{signal_id}/evidence")
    def get_signal_evidence(signal_id: str) -> dict[str, Any]:
        evidence = store.list_evidence(signal_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="evidence not found")

        links = []
        for item in evidence:
            event = store.get(item.event_id)
            links.append(
                {
                    "evidence": item.as_dict(),
                    "source_event": None if event is None else event.as_dict(),
                }
            )

        return {
            "signal_id": signal_id,
            "links": links,
        }

    @app.get("/v1/evidence/graph")
    def evidence_graph(
        limit: int = Query(default=config.max_query_limit, ge=1, le=config.max_query_limit),
    ) -> dict[str, object]:
        graph = EvidenceGraph()
        events = store.list_events(limit)
        signals = store.list_signals(limit)

        for event in events:
            graph.add_event(event)

        for signal in signals:
            graph.add_signal(signal)
            for evidence in store.list_evidence(signal.signal_id):
                graph.add_evidence(evidence)

        return graph.as_dict()

    @app.get("/v1/evidence/manifest/{signal_id}")
    def evidence_manifest(signal_id: str) -> dict[str, object]:
        signal = store.get_signal(signal_id)
        if signal is None:
            raise HTTPException(status_code=404, detail="signal not found")
        evidence = store.list_evidence(signal_id)
        event = store.get(signal.event_id)
        fingerprint_payload = {
            "event": event.as_dict() if event is not None else None,
            "signal": signal.as_dict(),
            "evidence": [item.as_dict() for item in evidence],
            "thresholds": {
                "biomarker_x_threshold": config.biomarker_x_threshold,
                "heart_rate_threshold": config.heart_rate_threshold,
            },
        }
        content_fingerprint = sha256(
            json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        manifest = build_manifest(
            dataset="sqlite-event-store",
            detector_version=signal.detector_version,
            input_ids=[signal.event_id],
            signal_ids=[signal.signal_id],
            evidence_ids=[item.evidence_id for item in evidence],
            content_fingerprint=content_fingerprint,
        )
        return manifest.as_dict()

    @app.get("/v1/registry")
    def registry() -> dict[str, object]:
        items = Registry().list()
        return {"count": len(items), "items": [item.as_dict() for item in items]}

    @app.get("/v1/audit")
    def audit_log(
        limit: int = Query(default=min(100, config.max_query_limit), ge=1, le=config.max_query_limit),
    ) -> dict[str, object]:
        records = store.list_audit(limit)
        return {"count": len(records), "records": records}

    @app.post("/v1/ai-guard/assess")
    def ai_guard(request: ModelGuardRequest) -> dict[str, object]:
        try:
            result = assess_model(
                ModelSpec(
                    model_id=request.model_id,
                    version=request.version,
                    context_of_use=request.context_of_use,
                    risk_tier=request.risk_tier,
                    validation_status=request.validation_status,
                ),
                request.reference,
                request.current,
                missing_reference=request.missing_reference,
                missing_current=request.missing_current,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return {
            "model": request.model_dump(
                exclude={
                    "reference",
                    "current",
                    "missing_reference",
                    "missing_current",
                }
            ),
            "assessment": {
                "status": result.status,
                "risk_flags": result.risk_flags,
                "metrics": result.metrics,
            },
        }

    @app.post("/v1/digital-measures/validate")
    def digital_measure(request: DigitalMeasureRequest) -> dict[str, object]:
        try:
            result = validate_digital_measure(
                request.measure_id,
                request.values,
                expected_min=request.expected_min,
                expected_max=request.expected_max,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return result.as_dict()

    @app.post("/v1/trial-integrity/sites/{site_id}/assess")
    def trial_integrity(
        site_id: str,
        events: list[TrialEventRequest],
    ) -> dict[str, object]:
        if not events:
            raise HTTPException(status_code=422, detail="events must be non-empty")

        domain_events = [
            TrialEvent(
                event_id=event.event_id,
                site_id=event.site_id,
                timestamp=event.timestamp,
                event_type=event.event_type,
                complete=event.complete,
                protocol_deviation=event.protocol_deviation,
            )
            for event in events
        ]

        try:
            result = assess_site(site_id, domain_events)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return result.as_dict()

    @app.get("/v1/lifecycle/{candidate_id}")
    def lifecycle(candidate_id: str) -> dict[str, object]:
        try:
            snapshots = simulate_lifecycle(candidate_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return {
            "candidate_id": candidate_id,
            "snapshots": [snapshot.as_dict() for snapshot in snapshots],
            "safety_boundary": (
                "workflow simulation only; no clinical or regulatory decision is produced"
            ),
        }

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard() -> str:
        dashboard_path = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
        if not dashboard_path.exists():
            raise HTTPException(status_code=404, detail="dashboard not found")
        return dashboard_path.read_text(encoding="utf-8")

    @app.get("/v1/scenarios")
    def list_scenarios() -> dict[str, object]:
        return {"count": len(SCENARIOS), "scenarios": SCENARIOS}

    @app.post("/v1/scenarios/{scenario}/run")
    def run_synthetic_scenario(scenario: str, seed: int = Query(default=42, ge=0, le=1_000_000)) -> dict[str, object]:
        try:
            return run_scenario(scenario, seed).as_dict()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/config")
    def config_summary() -> dict[str, object]:
        return {
            "environment": config.environment,
            "database_path": str(config.database_path),
            "thresholds": {
                "biomarker_x": config.biomarker_x_threshold,
                "heart_rate": config.heart_rate_threshold,
            },
            "safety_boundary": "configuration is for synthetic portfolio workflows only",
        }

    @app.get("/v1/interop/fhir/events/{event_id}")
    def fhir_event(event_id: str) -> dict[str, object]:
        event = store.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="event not found")
        return to_fhir_observation(event)

    @app.get("/v1/interop/omop/events/{event_id}")
    def omop_event(event_id: str) -> dict[str, object]:
        event = store.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="event not found")
        return to_omop_measurements(event)

    return app


app = create_app()
