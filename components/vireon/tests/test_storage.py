from __future__ import annotations
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from vireon.core.models import EventType, EvidenceLink, PharmaEvent, Signal
from vireon.storage.sqlite import EventStore

class StorageTests(unittest.TestCase):
    def _event(self) -> PharmaEvent:
        return PharmaEvent("E-PERSIST-001", "P-001", "S-01", EventType.VITAL,
                            datetime.now(timezone.utc)-timedelta(minutes=1), {"heart_rate":74.0}, "test")
    def test_event_survives_store_recreation(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/"nested"/"vireon.db"; original=self._event()
            EventStore(database).save(original); restored=EventStore(database).get(original.event_id)
            self.assertIsNotNone(restored); assert restored is not None
            self.assertEqual(restored.as_dict(), original.as_dict())
    def test_signal_evidence_and_audit_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/"vireon.db"; store=EventStore(database); event=self._event(); store.save(event)
            signal=Signal("SIG-E-PERSIST-001",event.event_id,"test_signal","moderate","test","test/1.0",datetime.now(timezone.utc))
            store.save_signal(signal)
            store.save_evidence(EvidenceLink("EVD-SIG-E-PERSIST-001",signal.signal_id,event.event_id,"detected_from",signal.detector_version,signal.detected_at))
            restored=EventStore(database)
            self.assertEqual(restored.get_signal(signal.signal_id).as_dict(), signal.as_dict())
            self.assertEqual(len(restored.list_evidence(signal.signal_id)),1)
            self.assertGreaterEqual(len(restored.list_audit()),3)
    def test_signal_identity_cannot_drift_after_evidence_is_linked(self):
        with tempfile.TemporaryDirectory() as directory:
            store=EventStore(Path(directory)/"vireon.db")
            event=self._event(); store.save(event)
            other=PharmaEvent("E-PERSIST-002", None, "S-02", EventType.VITAL, event.timestamp, {"heart_rate":80.0}, "test")
            store.save(other)
            signal=Signal("SIG-STABLE", event.event_id, "test_signal", "moderate", "test", "test/1.0", datetime.now(timezone.utc))
            store.save_signal(signal)
            store.save_evidence(EvidenceLink("EVD-STABLE", signal.signal_id, event.event_id, "detected_from", signal.detector_version, signal.detected_at))
            changed=Signal(signal.signal_id, other.event_id, signal.signal_type, signal.severity, signal.reason, signal.detector_version, signal.detected_at)
            with self.assertRaisesRegex(ValueError, "after evidence is linked"):
                store.save_signal(changed)

    def test_event_ordering_uses_actual_time_across_offsets(self):
        with tempfile.TemporaryDirectory() as directory:
            store=EventStore(Path(directory)/"vireon.db")
            older=PharmaEvent("E-OFFSET-OLD", None, "S-01", EventType.VITAL, datetime.fromisoformat("2025-01-01T10:00:00+02:00"), {"heart_rate":70.0}, "test")
            newer=PharmaEvent("E-OFFSET-NEW", None, "S-01", EventType.VITAL, datetime.fromisoformat("2025-01-01T09:30:00+00:00"), {"heart_rate":80.0}, "test")
            store.save(older); store.save(newer)
            ordered=store.list_events(2)
            self.assertEqual([event.event_id for event in ordered], ["E-OFFSET-NEW", "E-OFFSET-OLD"])

    def test_save_updates_existing_event(self):
        with tempfile.TemporaryDirectory() as directory:
            store=EventStore(Path(directory)/"vireon.db"); event=self._event(); store.save(event)
            updated=PharmaEvent(event.event_id,event.patient_id,event.site_id,event.event_type,event.timestamp,{"heart_rate":82.0},event.source)
            store.save(updated); restored=store.get(event.event_id)
            self.assertIsNotNone(restored); assert restored is not None
            self.assertEqual(restored.values["heart_rate"],82.0)

if __name__=="__main__": unittest.main()
