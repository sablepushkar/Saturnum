from datetime import datetime, timezone
import unittest

from vireon.core.models import EventType, PharmaEvent
from vireon.signal_engine import detect_signals


class StudyAInputBoundaryTests(unittest.TestCase):
    def event(self, values):
        return PharmaEvent(
            event_id="EV-STUDY-A",
            patient_id=None,
            site_id="SITE-DEMO",
            event_type=EventType.LAB_RESULT,
            timestamp=datetime.now(timezone.utc),
            values=values,
            source="synthetic-test",
        )

    def test_extreme_integer_value_does_not_crash_detection(self):
        event = self.event({"biomarker_x": 10 ** 10000})
        self.assertEqual(detect_signals([event]), [])

    def test_non_finite_threshold_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite number"):
            detect_signals([], biomarker_x_threshold=float("nan"))

    def test_extreme_threshold_conversion_is_reported_cleanly(self):
        with self.assertRaisesRegex(ValueError, "finite number"):
            detect_signals([], heart_rate_threshold=10 ** 10000)

    def test_normal_threshold_signal_still_works(self):
        event = self.event({"biomarker_x": 140})
        signals = detect_signals([event])
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, "biomarker_x_high")


if __name__ == "__main__":
    unittest.main()
