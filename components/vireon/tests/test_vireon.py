from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from vireon.ai_guard import ModelSpec, assess_model
from vireon.core.models import EventType, PharmaEvent
from vireon.core.validation import EventValidationError, validate_event
from vireon.digital_measures import validate_digital_measure
from vireon.evidence_graph import EvidenceGraph
from vireon.lifecycle import LifecycleStage, simulate_lifecycle
from vireon.signal_engine import detect_signals
from vireon.trial_integrity import TrialEvent, assess_site


class VireonTests(unittest.TestCase):
    def _event(self, values=None) -> PharmaEvent:
        return PharmaEvent(
            "E-001",
            "P-001",
            "S-01",
            EventType.LAB_RESULT,
            datetime.now(timezone.utc) - timedelta(minutes=1),
            values or {"biomarker_x": 135.0},
            "test",
        )

    def test_future_timestamp_is_rejected(self):
        event = self._event()
        future = PharmaEvent(
            event.event_id,
            event.patient_id,
            event.site_id,
            event.event_type,
            datetime.now(timezone.utc) + timedelta(minutes=5),
            event.values,
            event.source,
        )

        with self.assertRaises(EventValidationError):
            validate_event(future)

    def test_non_finite_event_value_is_rejected(self):
        with self.assertRaises(EventValidationError):
            validate_event(self._event({"biomarker_x": float("nan")}))

    def test_boolean_measurement_does_not_trigger_numeric_signal(self):
        event = self._event({"biomarker_x": True})
        self.assertEqual(detect_signals([event]), [])

    def test_signal_version_and_graph_are_deterministic(self):
        event = self._event()
        signal = detect_signals([event])[0]

        self.assertEqual(signal.detector_version, "threshold-rules/0.2")

        graph = EvidenceGraph()
        graph.add_event(event)
        graph.add_signal(signal)
        graph.add_signal(signal)

        self.assertEqual(len(graph.nodes), 2)
        self.assertEqual(len(graph.edges), 1)

    def test_ai_guard_flags_shift(self):
        result = assess_model(
            ModelSpec("demo", "1", "research", "medium", "validated"),
            [100, 100, 100],
            [130, 130, 140],
        )
        self.assertIn("distribution_mean_shift", result.risk_flags)

    def test_digital_measure_all_missing_is_review(self):
        result = validate_digital_measure("m", [None, None])
        self.assertIn("no_observed_values", result.flags)

    def test_trial_integrity_rejects_wrong_site(self):
        with self.assertRaises(ValueError):
            assess_site(
                "S-01",
                [
                    TrialEvent(
                        "1",
                        "S-02",
                        datetime.now(timezone.utc),
                        "visit",
                    )
                ],
            )

    def test_trial_integrity_rejects_future_event(self):
        with self.assertRaises(ValueError):
            assess_site(
                "S-01",
                [
                    TrialEvent(
                        "1",
                        "S-01",
                        datetime.now(timezone.utc) + timedelta(minutes=5),
                        "visit",
                    )
                ],
            )

    def test_lifecycle_has_all_stages(self):
        result = simulate_lifecycle("C")
        self.assertEqual(len(result), len(LifecycleStage))
        self.assertEqual(result[-1].stage, LifecycleStage.POST_MARKET)


if __name__ == "__main__":
    unittest.main()
