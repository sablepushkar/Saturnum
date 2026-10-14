import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from vireon.analytics import distribution_summary, summarize, z_score
from vireon.evidence_manifest import build_manifest
from vireon.registry import Registry, RegistryItem, RegistryStatus
from vireon.scenarios import run_scenario
from vireon.api import create_app


class V2FeatureTests(unittest.TestCase):
    def test_analytics(self):
        self.assertEqual(summarize([1.0, None, 3.0])["missing"], 1)
        self.assertAlmostEqual(z_score(12, [10, 11, 12, 13]), 0.4472135955, places=8)
        self.assertIn("standardized_shift", distribution_summary([1, 2], [3, 4]))

    def test_manifest_is_reproducible(self):
        a = build_manifest("demo", "threshold-rules/0.2", ["e1"], ["s1"], ["v1"])
        b = build_manifest("demo", "threshold-rules/0.2", ["e1"], ["s1"], ["v1"])
        self.assertEqual(a.manifest_id, b.manifest_id)

    def test_manifest_identity_includes_content_fingerprint(self):
        base = ("demo", "threshold-rules/0.2", ["e1"], ["s1"], ["v1"])
        first = build_manifest(*base, content_fingerprint="content-a")
        second = build_manifest(*base, content_fingerprint="content-b")
        self.assertNotEqual(first.manifest_id, second.manifest_id)

    def test_registry_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            registry = Registry(path)
            registry.upsert(RegistryItem("model-1", "1.0", "model", "demo", RegistryStatus.ACTIVE, "monitoring", "medium", "2026-01-01"))
            self.assertEqual(registry.list()[0].item_id, "model-1")

    def test_scenarios(self):
        result = run_scenario("biomarker-signal")
        self.assertGreaterEqual(result.signal_count, 1)
        self.assertEqual(result.safety_boundary.startswith("Synthetic"), True)

    def test_api_scenario_and_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = TestClient(create_app(Path(tmp) / "test.db"))
            scenarios = client.get("/v1/scenarios")
            self.assertEqual(scenarios.status_code, 200)
            self.assertIn("biomarker-signal", scenarios.json()["scenarios"])
            run = client.post("/v1/scenarios/biomarker-signal/run")
            self.assertEqual(run.status_code, 200)
            client.post("/v1/events", json={
                "event_id": "MAN-E1", "patient_id": "P1", "site_id": "S1",
                "event_type": "lab_result",
                "timestamp": "2026-09-21T03:00:00+00:00",
                "values": {"biomarker_x": 140}, "source": "test"
            })
            client.post("/v1/signals/detect")
            manifest = client.get("/v1/evidence/manifest/SIG-MAN-E1")
            self.assertEqual(manifest.status_code, 200)
            self.assertTrue(manifest.json()["manifest_id"].startswith("MAN-"))
            dashboard = client.get("/dashboard")
            self.assertEqual(dashboard.status_code, 200)
            self.assertIn("Scenario Explorer", dashboard.text)
            registry = client.get("/v1/registry")
            self.assertEqual(registry.status_code, 200)


if __name__ == "__main__":
    unittest.main()
