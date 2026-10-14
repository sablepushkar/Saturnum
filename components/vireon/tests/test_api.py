from __future__ import annotations
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient
from vireon.api import create_app
from vireon.config import VireonConfig

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir=tempfile.TemporaryDirectory()
        self.client=TestClient(create_app(Path(self.tempdir.name)/"test.db"))
    def tearDown(self): self.tempdir.cleanup()
    def _event(self):
        return {"event_id":"E-API-001","patient_id":"P-001","site_id":"S-01","event_type":"lab_result",
                "timestamp":(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat(),
                "values":{"biomarker_x":135.0},"source":"test"}
    def test_configured_query_limit_is_enforced(self):
        app = create_app(Path(self.tempdir.name)/"limited.db", config=VireonConfig(max_query_limit=2))
        client = TestClient(app)
        self.assertEqual(client.get("/v1/events?limit=2").status_code, 200)
        self.assertEqual(client.get("/v1/events?limit=3").status_code, 422)

    def test_non_finite_threshold_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite number"):
            VireonConfig(biomarker_x_threshold=float("nan"))

    def test_health_and_event(self):
        self.assertEqual(self.client.get("/health").status_code,200)
        self.assertEqual(self.client.post("/v1/events",json=self._event()).status_code,201)
        self.assertEqual(self.client.get("/v1/events/E-API-001").status_code,200)
    def test_graph_evidence_signal_and_audit(self):
        self.client.post("/v1/events",json=self._event())
        self.assertEqual(self.client.post("/v1/signals/detect").json()["signal_count"],1)
        self.assertEqual(self.client.get("/v1/signals").json()["count"],1)
        self.assertEqual(self.client.get("/v1/signals/SIG-E-API-001/evidence").status_code,200)
        self.assertGreaterEqual(len(self.client.get("/v1/evidence/graph").json()["nodes"]),3)
        self.assertGreaterEqual(self.client.get("/v1/audit").json()["count"],3)
    def test_ai_guard(self):
        r=self.client.post("/v1/ai-guard/assess",json={"model_id":"demo","version":"1","context_of_use":"research monitoring",
          "risk_tier":"medium","validation_status":"validated","reference":[100,100,100],"current":[130,130,130]})
        self.assertEqual(r.status_code,200); self.assertIn("distribution_mean_shift",r.json()["assessment"]["risk_flags"])
    def test_digital_measure(self):
        r=self.client.post("/v1/digital-measures/validate",json={"measure_id":"wearable-activity","values":[1,None,2,3]})
        self.assertEqual(r.status_code,200); self.assertIn("high_missingness",r.json()["flags"])
    def test_trial_integrity_and_lifecycle(self):
        now=datetime.now(timezone.utc).isoformat()
        r=self.client.post("/v1/trial-integrity/sites/S-01/assess",json=[{"event_id":"1","site_id":"S-01","timestamp":now,
          "event_type":"visit","complete":True,"protocol_deviation":True}])
        self.assertEqual(r.status_code,200); self.assertEqual(len(self.client.get("/v1/lifecycle/CAND-001").json()["snapshots"]),8)
    def test_interop_boundaries(self):
        self.client.post("/v1/events",json=self._event())
        fhir=self.client.get("/v1/interop/fhir/events/E-API-001"); omop=self.client.get("/v1/interop/omop/events/E-API-001")
        self.assertEqual(fhir.status_code,200); self.assertEqual(fhir.json()["resourceType"],"Observation")
        self.assertEqual(omop.status_code,200); self.assertEqual(omop.json()["mapping_status"],"unmapped_local_keys")

if __name__=="__main__": unittest.main()
