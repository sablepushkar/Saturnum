#!/usr/bin/env python3
"""Acoustic-B-Box: compact event-communication simulator.

Prototype only. Medical examples are synthetic and operational response values
are simulation parameters, not clinical guidance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import time
import uuid
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("acoustic_bbox.db")
DEFAULT_WAV = Path("acoustic_event.wav")
SAMPLE_RATE = 48_000
GGWAVE_PROTOCOL = 1
GGWAVE_VOLUME = 20
PROJECT_VERSION = "A.B.B Q3"

CATEGORIES = {
    "MEDICAL": "Clinical event",
    "EQUIPMENT": "Equipment problem",
    "LOGISTICS": "Supply / logistics request",
    "ENVIRONMENT": "Environment alert",
    "OPERATIONS": "Workflow notification",
    "SYSTEM": "System / device status",
}

PRIORITIES = {
    "P0": "Critical / immediate attention",
    "P1": "Urgent / rapid attention",
    "P2": "Priority / soon",
    "P3": "Routine",
    "P4": "Informational",
}

DEPARTMENTS = [
    "Emergency",
    "ICU",
    "Ward A",
    "Pharmacy",
    "Laboratory",
    "Maintenance",
    "Operations",
]

EVENT_FLOW = {
    "CREATED": {"DISPATCHED"},
    "DISPATCHED": {"DELIVERED", "FAILED"},
    "FAILED": {"DISPATCHED"},
    "DELIVERED": {"ACKNOWLEDGED"},
    "ACKNOWLEDGED": {"IN_PROGRESS", "RESOLVED"},
    "IN_PROGRESS": {"RESOLVED"},
    "RESOLVED": set(),
}

SCENARIOS = {
    "1": {
        "category": "MEDICAL",
        "priority": "P1",
        "event_type": "VITAL_ALERT",
        "department": "ICU",
        "description": "Synthetic patient-monitor alert",
        "response_units": 2,
        "roles": ["department_responder"],
        "data": {"subject_id": "MOCK-001", "monitor_status": "ALERT"},
        "failures_before_success": 0,
    },
    "2": {
        "category": "EQUIPMENT",
        "priority": "P1",
        "event_type": "DEVICE_FAILURE",
        "department": "Emergency",
        "description": "Synthetic monitor/device failure",
        "response_units": 1,
        "roles": ["technical_responder"],
        "data": {"device_id": "SIM-MONITOR-07", "fault": "NO_SIGNAL"},
        "failures_before_success": 1,
    },
    "3": {
        "category": "LOGISTICS",
        "priority": "P2",
        "event_type": "SUPPLY_REQUIRED",
        "department": "Pharmacy",
        "description": "Synthetic supply request",
        "response_units": 1,
        "roles": ["assigned_operator"],
        "data": {"item": "DEMO-SUPPLY", "quantity": 3},
        "failures_before_success": 0,
    },
    "4": {
        "category": "ENVIRONMENT",
        "priority": "P2",
        "event_type": "TEMPERATURE_ALERT",
        "department": "Ward A",
        "description": "Synthetic environment alert",
        "response_units": 1,
        "roles": ["facility_responder"],
        "data": {"zone": "WARD-A-STORAGE", "condition": "OUT_OF_RANGE_DEMO"},
        "failures_before_success": 0,
    },
    "5": {
        "category": "OPERATIONS",
        "priority": "P3",
        "event_type": "WORKFLOW_NOTIFICATION",
        "department": "Operations",
        "description": "Synthetic workflow notification",
        "response_units": 0,
        "roles": ["department_queue"],
        "data": {"workflow": "SHIFT_HANDOFF"},
        "failures_before_success": 0,
    },
    "6": {
        "category": "SYSTEM",
        "priority": "P4",
        "event_type": "DEVICE_STATUS",
        "department": "Maintenance",
        "description": "Synthetic device status update",
        "response_units": 0,
        "roles": [],
        "data": {"device_id": "SIM-GATEWAY-01", "status": "HEALTHY"},
        "failures_before_success": 0,
    },
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def new_id(prefix: str = "BX") -> str:
    return f"{prefix}-{uuid.uuid4().hex.upper()}"


@dataclass
class Event:
    event_id: str
    created_at: str
    category: str
    priority: str
    event_type: str
    department: str
    description: str
    source_device: str = "SIM-DEVICE-01"
    status: str = "CREATED"
    response_units: int = 0
    response_roles: list[str] = field(default_factory=list)
    attempts: int = 0
    transport: str = "SIMULATOR"
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)


def validate_event(event: Event) -> None:
    if event.category not in CATEGORIES:
        raise ValueError(f"Unknown category: {event.category}")
    if event.priority not in PRIORITIES:
        raise ValueError(f"Unknown priority: {event.priority}")
    if event.department not in DEPARTMENTS:
        raise ValueError(f"Unknown department: {event.department}")
    if not isinstance(event.event_id, str) or not event.event_id.strip():
        raise ValueError("event_id must be a non-empty string")
    if not isinstance(event.description, str) or not event.description.strip():
        raise ValueError("description must be a non-empty string")
    if len(event.description) > 1000:
        raise ValueError("description cannot exceed 1000 characters")
    if not isinstance(event.source_device, str) or not event.source_device.strip():
        raise ValueError("source_device must be a non-empty string")
    if isinstance(event.response_units, bool) or not isinstance(event.response_units, int) or event.response_units < 0:
        raise ValueError("response_units must be a non-negative integer")
    if not isinstance(event.response_roles, list) or any(
        not isinstance(role, str) or not role.strip() for role in event.response_roles
    ):
        raise ValueError("response_roles must be a list of non-empty strings")
    if not isinstance(event.data, dict):
        raise ValueError("event data must be a dictionary")
    def is_strict_json(value: Any) -> bool:
        if value is None or isinstance(value, (str, bool)):
            return True
        if isinstance(value, int) and not isinstance(value, bool):
            return True
        if isinstance(value, float):
            return math.isfinite(value)
        if isinstance(value, list):
            return all(is_strict_json(item) for item in value)
        if isinstance(value, dict):
            return all(isinstance(key, str) and is_strict_json(item) for key, item in value.items())
        return False

    if not is_strict_json(event.data):
        raise ValueError("event data must contain strict JSON-compatible values")
    try:
        json.dumps(event.data, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError("event data must contain strict JSON-compatible values") from exc


def payload_for(event: Event) -> dict[str, Any]:
    validate_event(event)
    return {
        "bbox_version": PROJECT_VERSION,
        "message_id": event.event_id,
        "created_at": event.created_at,
        "category": event.category,
        "priority": event.priority,
        "event_type": event.event_type,
        "department": event.department,
        "source_device": event.source_device,
        "description": event.description,
        "response": {
            "units_demo": event.response_units,
            "roles_demo": event.response_roles,
        },
        "data": event.data,
    }


def payload_bytes(event: Event) -> bytes:
    return json.dumps(
        payload_for(event),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def payload_hash(event: Event) -> str:
    return hashlib.sha256(payload_bytes(event)).hexdigest()


def validate_decoded_packet(packet: Any) -> dict[str, Any]:
    """Validate the minimum envelope contract for a decoded transport packet."""
    if not isinstance(packet, dict):
        raise ValueError("Decoded packet must be a JSON object.")
    message_id = packet.get("message_id")
    if packet.get("bbox_version") != PROJECT_VERSION or not isinstance(message_id, str) or not message_id.strip():
        raise ValueError(f"Decoded packet is not a valid Acoustic-B-Box event.")
    return packet


def transition(event: Event, new_status: str) -> None:
    if new_status not in EVENT_FLOW.get(event.status, set()):
        raise ValueError(f"Invalid event transition: {event.status} -> {new_status}")
    event.status = new_status
    if new_status == "ACKNOWLEDGED":
        event.acknowledged_at = now()
    elif new_status == "RESOLVED":
        event.resolved_at = now()


class Store:
    """Tiny SQLite persistence layer for the sample system."""

    def __init__(self, path: Path = DB_PATH):
        self.path = Path(path)
        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                event_type TEXT NOT NULL,
                department TEXT NOT NULL,
                description TEXT NOT NULL,
                source_device TEXT NOT NULL,
                status TEXT NOT NULL,
                response_units INTEGER NOT NULL,
                response_roles TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                transport TEXT NOT NULL,
                acknowledged_at TEXT,
                resolved_at TEXT,
                payload_sha256 TEXT NOT NULL,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transmissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                transport TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                success INTEGER NOT NULL,
                detail TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                at TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                department TEXT NOT NULL,
                status TEXT NOT NULL,
                last_seen TEXT NOT NULL
            );
            """
        )
        self.seed_devices()

    def seed_devices(self) -> None:
        for i, department in enumerate(DEPARTMENTS, 1):
            self.con.execute(
                "INSERT OR IGNORE INTO devices VALUES (?, ?, ?, ?)",
                (f"SIM-DEVICE-{i:02d}", department, "ONLINE", now()),
            )
        self.con.commit()

    def save_event(self, event: Event) -> None:
        self.con.execute(
            """
            INSERT INTO events (
                event_id, created_at, category, priority, event_type, department,
                description, source_device, status, response_units, response_roles,
                attempts, transport, acknowledged_at, resolved_at, payload_sha256,
                data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                created_at=excluded.created_at,
                category=excluded.category,
                priority=excluded.priority,
                event_type=excluded.event_type,
                department=excluded.department,
                description=excluded.description,
                source_device=excluded.source_device,
                status=excluded.status,
                response_units=excluded.response_units,
                response_roles=excluded.response_roles,
                attempts=excluded.attempts,
                transport=excluded.transport,
                acknowledged_at=excluded.acknowledged_at,
                resolved_at=excluded.resolved_at,
                payload_sha256=excluded.payload_sha256,
                data_json=excluded.data_json
            """,
            (
                event.event_id,
                event.created_at,
                event.category,
                event.priority,
                event.event_type,
                event.department,
                event.description,
                event.source_device,
                event.status,
                event.response_units,
                json.dumps(event.response_roles),
                event.attempts,
                event.transport,
                event.acknowledged_at,
                event.resolved_at,
                payload_hash(event),
                json.dumps(event.data, sort_keys=True),
            ),
        )
        self.con.commit()

    def audit(
        self,
        event_id: str,
        action: str,
        details: str = "",
        actor: str = "SIM_ENGINE",
    ) -> None:
        self.con.execute(
            "INSERT INTO audit_log(event_id, at, action, actor, details) VALUES (?, ?, ?, ?, ?)",
            (event_id, now(), action, actor, details),
        )
        self.con.commit()

    def transmission(
        self,
        event_id: str,
        transport: str,
        attempt: int,
        success: bool,
        detail: str,
        started: str,
        finished: str,
    ) -> None:
        self.con.execute(
            """
            INSERT INTO transmissions
                (event_id, transport, attempt, started_at, finished_at, success, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, transport, attempt, started, finished, int(success), detail),
        )
        self.con.commit()

    def recent_events(self, limit: int = 12):
        return self.con.execute(
            "SELECT * FROM events ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    def timeline(self, event_id: str):
        return self.con.execute(
            "SELECT * FROM audit_log WHERE event_id=? ORDER BY id",
            (event_id,),
        ).fetchall()

    def summary(self) -> dict[str, int]:
        rows = self.con.execute(
            "SELECT status, COUNT(*) AS n FROM events GROUP BY status"
        ).fetchall()
        result = {row["status"]: row["n"] for row in rows}
        result["TOTAL"] = sum(result.values())
        result["ACTIVE"] = sum(
            result.get(status, 0)
            for status in (
                "CREATED",
                "DISPATCHED",
                "DELIVERED",
                "ACKNOWLEDGED",
                "IN_PROGRESS",
                "FAILED",
            )
        )
        result["DEVICES_ONLINE"] = self.con.execute(
            "SELECT COUNT(*) FROM devices WHERE status='ONLINE'"
        ).fetchone()[0]
        return result

    def load_event(self, event_id: str) -> Optional[Event]:
        row = self.con.execute(
            "SELECT * FROM events WHERE event_id=?",
            (event_id,),
        ).fetchone()
        if not row:
            return None
        return Event(
            event_id=row["event_id"],
            created_at=row["created_at"],
            category=row["category"],
            priority=row["priority"],
            event_type=row["event_type"],
            department=row["department"],
            description=row["description"],
            source_device=row["source_device"],
            status=row["status"],
            response_units=row["response_units"],
            response_roles=json.loads(row["response_roles"]),
            attempts=row["attempts"],
            transport=row["transport"],
            acknowledged_at=row["acknowledged_at"],
            resolved_at=row["resolved_at"],
            data=json.loads(row["data_json"]),
        )

    def close(self) -> None:
        self.con.close()


def create_scenario(choice: str) -> Event:
    cfg = SCENARIOS.get(choice)
    if not cfg:
        raise ValueError("Unknown scenario.")
    event = Event(
        event_id=new_id(),
        created_at=now(),
        category=cfg["category"],
        priority=cfg["priority"],
        event_type=cfg["event_type"],
        department=cfg["department"],
        description=cfg["description"],
        response_units=cfg["response_units"],
        response_roles=list(cfg["roles"]),
        data=dict(cfg["data"]),
    )
    validate_event(event)
    return event


class SimulatorTransport:
    """Deterministic transport used for a complete hardware-free demonstration."""

    name = "SIMULATOR"

    def __init__(self, planned_failures: int = 0):
        self.remaining_failures = planned_failures

    def send(self) -> tuple[bool, str]:
        time.sleep(0.05)
        if self.remaining_failures > 0:
            self.remaining_failures -= 1
            return False, "SIMULATED_DELIVERY_FAILURE"
        return True, "DELIVERY_CONFIRMED"


class AcousticWavTransport:
    """Optional GGWave adapter that creates and reads ordinary WAV files."""

    def encode_wav(self, event: Event, output: Path = DEFAULT_WAV) -> Path:
        try:
            import ggwave
        except ImportError as exc:
            raise RuntimeError(
                "Install optional GGWave support with: pip install ggwave"
            ) from exc

        message = json.dumps(
            payload_for(event),
            separators=(",", ":"),
            sort_keys=True,
        )
        waveform = ggwave.encode(
            message,
            protocolId=GGWAVE_PROTOCOL,
            volume=GGWAVE_VOLUME,
        )

        with wave.open(str(output), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(waveform)

        return output

    def decode_wav(self, source: Path) -> dict[str, Any]:
        try:
            import ggwave
        except ImportError as exc:
            raise RuntimeError(
                "Install optional GGWave support with: pip install ggwave"
            ) from exc

        with wave.open(str(source), "rb") as wav:
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                raise ValueError("Expected a mono 16-bit PCM WAV file.")
            if wav.getframerate() != SAMPLE_RATE:
                raise ValueError(f"Expected {SAMPLE_RATE} Hz WAV audio.")
            frames = wav.readframes(wav.getnframes())

        instance = ggwave.init()
        try:
            decoded = ggwave.decode(instance, frames)
        finally:
            ggwave.free(instance)

        if not decoded:
            raise RuntimeError("GGWave could not decode this WAV file.")

        packet = json.loads(decoded.decode("utf-8"))
        return validate_decoded_packet(packet)


def complete_simulated_event(
    store: Store,
    event: Event,
    transport: SimulatorTransport,
    retry_limit: int = 2,
) -> None:
    """Run the sample lifecycle, including deterministic retries and audit logs."""
    store.save_event(event)
    store.audit(event.event_id, "CREATED", event.category)

    delivered = False

    for attempt in range(1, retry_limit + 2):
        transition(event, "DISPATCHED")
        event.attempts = attempt
        event.transport = transport.name
        started = now()
        store.save_event(event)
        store.audit(event.event_id, "DISPATCHED", f"attempt={attempt}")

        success, detail = transport.send()
        finished = now()
        store.transmission(
            event.event_id,
            transport.name,
            attempt,
            success,
            detail,
            started,
            finished,
        )

        if success:
            transition(event, "DELIVERED")
            store.save_event(event)
            store.audit(event.event_id, "DELIVERED", f"attempt={attempt}")
            delivered = True
            break

        transition(event, "FAILED")
        store.save_event(event)
        store.audit(event.event_id, "DELIVERY_FAILED", detail)

        if attempt <= retry_limit:
            # Remain in FAILED; EVENT_FLOW explicitly permits FAILED -> DISPATCHED.
            store.save_event(event)
            store.audit(
                event.event_id,
                "RETRY_SCHEDULED",
                f"next_attempt={attempt + 1}",
            )

    if not delivered:
        store.audit(
            event.event_id,
            "ESCALATED",
            "simulation retry limit reached",
        )
        return

    transition(event, "ACKNOWLEDGED")
    store.save_event(event)
    store.audit(
        event.event_id,
        "ACKNOWLEDGED",
        "synthetic acknowledgement",
    )

    transition(event, "IN_PROGRESS")
    store.save_event(event)
    store.audit(
        event.event_id,
        "IN_PROGRESS",
        "synthetic response started",
    )

    time.sleep(0.05)

    transition(event, "RESOLVED")
    store.save_event(event)
    store.audit(
        event.event_id,
        "RESOLVED",
        "synthetic scenario completed",
    )


def print_event(event: Event) -> None:
    print(
        f"\n[{event.priority}] {event.event_id} | "
        f"{event.category} | {event.event_type}"
    )
    print(f"Department    : {event.department}")
    print(f"Status        : {event.status}")
    print(f"Description   : {event.description}")
    print(f"Response demo : {event.response_units} unit(s)")
    print(f"Roles demo    : {', '.join(event.response_roles) or 'none'}")
    print(f"Transport     : {event.transport}")
    print(f"Attempts      : {event.attempts}")
    print(f"Payload SHA256: {payload_hash(event)[:16]}...")


def show_dashboard(store: Store) -> None:
    summary = store.summary()

    print("\n=== ACOUSTIC-B-BOX | SAMPLE OPERATIONS DASHBOARD ===")
    print(
        f"Total events: {summary.get('TOTAL', 0)}   "
        f"Active: {summary.get('ACTIVE', 0)}   "
        f"Seeded demo devices (not live status): {summary.get('DEVICES_ONLINE', 0)}"
    )
    print("-" * 86)
    print("PRI | STATUS         | EVENT ID        | DEPARTMENT   | TYPE")
    print("-" * 86)

    rows = store.recent_events()
    for row in rows:
        print(
            f"{row['priority']:>3} | "
            f"{row['status']:<14} | "
            f"{row['event_id']:<15} | "
            f"{row['department']:<12} | "
            f"{row['event_type']}"
        )

    if not rows:
        print("No events yet.")


def show_timeline(store: Store, event_id: str) -> None:
    rows = store.timeline(event_id)
    print(f"\n=== TIMELINE: {event_id} ===")

    if not rows:
        print("Event not found or has no audit records.")
        return

    for row in rows:
        print(
            f"{row['at']} | "
            f"{row['action']:<16} | "
            f"{row['actor']:<10} | "
            f"{row['details']}"
        )


def run_scenario(store: Store) -> None:
    print("\nChoose a synthetic scenario:")
    for key, cfg in SCENARIOS.items():
        print(f"{key}. [{cfg['priority']}] {cfg['description']}")

    choice = input("Scenario: ").strip()
    event = create_scenario(choice)
    print_event(event)

    transport = SimulatorTransport(
        SCENARIOS[choice]["failures_before_success"]
    )
    complete_simulated_event(store, event, transport)

    print_event(event)
    print("\nScenario complete.")


def run_demo(store: Store) -> None:
    for key in SCENARIOS:
        event = create_scenario(key)
        transport = SimulatorTransport(
            SCENARIOS[key]["failures_before_success"]
        )
        print(f"\n>>> DEMO {key}: {event.description}")
        complete_simulated_event(store, event, transport)

    show_dashboard(store)


def run_self_test() -> None:
    event = create_scenario("1")
    assert event.priority in PRIORITIES
    assert event.category in CATEGORIES
    assert event.department in DEPARTMENTS

    encoded = payload_bytes(event)
    assert hashlib.sha256(encoded).hexdigest() == payload_hash(event)
    assert json.loads(encoded.decode("utf-8"))["message_id"] == event.event_id

    with __import__("tempfile").TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "test.db")
        simulated = create_scenario("2")
        complete_simulated_event(
            store,
            simulated,
            SimulatorTransport(planned_failures=1),
        )

        row = store.con.execute(
            "SELECT status, attempts FROM events WHERE event_id=?",
            (simulated.event_id,),
        ).fetchone()
        assert row["status"] == "RESOLVED"
        assert row["attempts"] == 2

        transmission_count = store.con.execute(
            "SELECT COUNT(*) FROM transmissions WHERE event_id=?",
            (simulated.event_id,),
        ).fetchone()[0]
        assert transmission_count == 2

        assert len(store.timeline(simulated.event_id)) >= 6
        store.close()

    print("SELF-TEST: PASS")
    print("✓ structured event + priority/category validation")
    print("✓ JSON payload + SHA-256 integrity hash")
    print("✓ SQLite persistence + audit trail")
    print("✓ delivery failure + retry path")
    print("✓ event lifecycle + acknowledgement + resolution")
    print("✓ no microphone/speaker required")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Acoustic-B-Box sample system"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run one synthetic scenario",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run all six synthetic scenarios",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Show stored events",
    )
    parser.add_argument(
        "--timeline",
        metavar="EVENT_ID",
        help="Show one event's audit timeline",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the hardware-free self-test",
    )
    parser.add_argument(
        "--encode-wav",
        metavar="EVENT_ID",
        help="Encode one stored event to a GGWave WAV file",
    )
    parser.add_argument(
        "--decode-wav",
        metavar="PATH",
        help="Decode a GGWave WAV file",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="SQLite database path",
    )
    parser.add_argument(
        "--wav-out",
        type=Path,
        default=DEFAULT_WAV,
        help="WAV output path",
    )
    args = parser.parse_args()

    if args.test:
        run_self_test()
        return

    if args.decode_wav:
        decoded = AcousticWavTransport().decode_wav(Path(args.decode_wav))
        print(json.dumps(decoded, indent=2))
        return

    store = Store(args.db)
    try:
        if args.dashboard:
            show_dashboard(store)

        elif args.timeline:
            show_timeline(store, args.timeline)

        elif args.demo:
            run_demo(store)

        elif args.simulate:
            run_scenario(store)
            show_dashboard(store)

        elif args.encode_wav:
            event = store.load_event(args.encode_wav)
            if not event:
                raise SystemExit("Event ID not found in database.")

            output = AcousticWavTransport().encode_wav(
                event,
                args.wav_out,
            )
            print(f"GGWave WAV created: {output}")
            return

        else:
            print("Acoustic-B-Box")
            print("1. Run sample hospital event")
            print("2. Run all demo scenarios")
            print("3. View dashboard")
            print("4. Self-test")

            choice = input("Select: ").strip()

            if choice == "1":
                run_scenario(store)
                show_dashboard(store)
            elif choice == "2":
                run_demo(store)
            elif choice == "3":
                show_dashboard(store)
            elif choice == "4":
                run_self_test()
            else:
                print("Invalid selection.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
