from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from ..core.models import EventType, EvidenceLink, PharmaEvent, Signal


class EventStore:
    """SQLite event, signal, provenance, and audit store for VIREON."""

    def __init__(self, database_path: str | Path = "vireon.db") -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES events(event_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_links (
                    evidence_id TEXT PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    detector_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(signal_id) REFERENCES signals(signal_id),
                    FOREIGN KEY(event_id) REFERENCES events(event_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    details TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_signals_event ON signals(event_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_signal ON evidence_links(signal_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(occurred_at)"
            )

    def _audit(
        self,
        connection: sqlite3.Connection,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, object],
    ) -> None:
        connection.execute(
            """
            INSERT INTO audit_log(
                action, entity_type, entity_id, occurred_at, details
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                action,
                entity_type,
                entity_id,
                datetime.now().astimezone().isoformat(),
                json.dumps(details, separators=(",", ":")),
            ),
        )

    def save(self, event: PharmaEvent) -> None:
        payload = json.dumps(event.as_dict(), separators=(",", ":"))

        with self._connect() as connection:
            existed = connection.execute(
                "SELECT 1 FROM events WHERE event_id = ?",
                (event.event_id,),
            ).fetchone()

            connection.execute(
                """
                INSERT INTO events(event_id, payload)
                VALUES (?, ?)
                ON CONFLICT(event_id) DO UPDATE SET payload = excluded.payload
                """,
                (event.event_id, payload),
            )

            self._audit(
                connection,
                "updated" if existed else "created",
                "event",
                event.event_id,
                {
                    "source": event.source,
                    "event_type": event.event_type.value,
                },
            )

    def get(self, event_id: str) -> PharmaEvent | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()

        return None if row is None else self._from_payload(json.loads(row["payload"]))

    def list_events(self, limit: int = 100) -> list[PharmaEvent]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM events
                ORDER BY julianday(json_extract(payload, '$.timestamp')) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._from_payload(json.loads(row["payload"])) for row in rows]

    def save_signal(self, signal: Signal) -> None:
        payload = json.dumps(signal.as_dict(), separators=(",", ":"))

        with self._connect() as connection:
            if connection.execute(
                "SELECT 1 FROM events WHERE event_id = ?",
                (signal.event_id,),
            ).fetchone() is None:
                raise ValueError("signal event_id does not exist")

            existing = connection.execute(
                "SELECT event_id, payload FROM signals WHERE signal_id = ?",
                (signal.signal_id,),
            ).fetchone()
            if existing is not None:
                prior_payload = json.loads(existing["payload"])
                has_evidence = connection.execute(
                    "SELECT 1 FROM evidence_links WHERE signal_id = ? LIMIT 1",
                    (signal.signal_id,),
                ).fetchone() is not None
                if has_evidence and (
                    existing["event_id"] != signal.event_id
                    or prior_payload.get("detector_version") != signal.detector_version
                ):
                    raise ValueError("cannot change a signal's event or detector version after evidence is linked")
            existed = existing is not None

            connection.execute(
                """
                INSERT INTO signals(signal_id, event_id, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(signal_id) DO UPDATE SET
                    event_id = excluded.event_id,
                    payload = excluded.payload
                """,
                (signal.signal_id, signal.event_id, payload),
            )

            self._audit(
                connection,
                "updated" if existed else "created",
                "signal",
                signal.signal_id,
                {
                    "event_id": signal.event_id,
                    "detector_version": signal.detector_version,
                },
            )

    def get_signal(self, signal_id: str) -> Signal | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM signals WHERE signal_id = ?",
                (signal_id,),
            ).fetchone()

        return (
            None
            if row is None
            else self._signal_from_payload(json.loads(row["payload"]))
        )

    def list_signals(self, limit: int = 1000) -> list[Signal]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM signals
                ORDER BY julianday(json_extract(payload, '$.detected_at')) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._signal_from_payload(json.loads(row["payload"])) for row in rows]

    def save_evidence(self, evidence: EvidenceLink) -> None:
        with self._connect() as connection:
            signal_row = connection.execute(
                "SELECT event_id FROM signals WHERE signal_id = ?",
                (evidence.signal_id,),
            ).fetchone()

            if signal_row is None:
                raise ValueError("evidence signal_id does not exist")

            if signal_row["event_id"] != evidence.event_id:
                raise ValueError(
                    "evidence event_id does not match the signal event_id"
                )

            connection.execute(
                """
                INSERT INTO evidence_links(
                    evidence_id, signal_id, event_id, relationship,
                    detector_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                    signal_id = excluded.signal_id,
                    event_id = excluded.event_id,
                    relationship = excluded.relationship,
                    detector_version = excluded.detector_version,
                    created_at = excluded.created_at
                """,
                (
                    evidence.evidence_id,
                    evidence.signal_id,
                    evidence.event_id,
                    evidence.relationship,
                    evidence.detector_version,
                    evidence.created_at.isoformat(),
                ),
            )

            self._audit(
                connection,
                "linked",
                "evidence",
                evidence.evidence_id,
                {
                    "signal_id": evidence.signal_id,
                    "event_id": evidence.event_id,
                },
            )

    def list_evidence(self, signal_id: str) -> list[EvidenceLink]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT evidence_id, signal_id, event_id, relationship,
                       detector_version, created_at
                FROM evidence_links
                WHERE signal_id = ?
                ORDER BY julianday(created_at) ASC
                """,
                (signal_id,),
            ).fetchall()

        return [
            EvidenceLink(
                evidence_id=row["evidence_id"],
                signal_id=row["signal_id"],
                event_id=row["event_id"],
                relationship=row["relationship"],
                detector_version=row["detector_version"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def list_audit(self, limit: int = 100) -> list[dict[str, object]]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT audit_id, action, entity_type, entity_id, occurred_at, details
                FROM audit_log
                ORDER BY audit_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "audit_id": row["audit_id"],
                "action": row["action"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "occurred_at": row["occurred_at"],
                "details": json.loads(row["details"]),
            }
            for row in rows
        ]

    @staticmethod
    def _from_payload(payload: dict[str, object]) -> PharmaEvent:
        values = payload["values"]
        if not isinstance(values, dict):
            raise ValueError("stored event values must be an object")

        return PharmaEvent(
            event_id=str(payload["event_id"]),
            patient_id=(
                None
                if payload.get("patient_id") is None
                else str(payload["patient_id"])
            ),
            site_id=str(payload["site_id"]),
            event_type=EventType(str(payload["event_type"])),
            timestamp=datetime.fromisoformat(str(payload["timestamp"])),
            values=values,
            source=str(payload["source"]),
        )

    @staticmethod
    def _signal_from_payload(payload: dict[str, object]) -> Signal:
        return Signal(
            signal_id=str(payload["signal_id"]),
            event_id=str(payload["event_id"]),
            signal_type=str(payload["signal_type"]),
            severity=str(payload["severity"]),
            reason=str(payload["reason"]),
            detector_version=str(payload["detector_version"]),
            detected_at=datetime.fromisoformat(str(payload["detected_at"])),
        )
