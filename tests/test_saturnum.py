import json
import subprocess
import sys
import unittest
from pathlib import Path

from saturnum import build_status_report

ROOT = Path(__file__).resolve().parents[1]


class SaturnumStatusTests(unittest.TestCase):
    def test_report_has_named_checks_and_explicit_scope_boundaries(self):
        report = build_status_report()
        self.assertEqual(report["project"], "Saturnum")
        self.assertEqual(report["report_schema_version"], 1)
        self.assertIn(report["overall_status"], {"pass", "fail"})
        names = {item["name"] for item in report["checks"]}
        self.assertIn("acoustic_component_source", names)
        self.assertIn("vireon_source", names)
        self.assertEqual(
            report["capability_boundaries"]["acoustic_hardware_round_trip"],
            "not_tested_by_this_report",
        )
        self.assertEqual(
            report["capability_boundaries"]["clinical_or_pharmaceutical_validation"],
            "not_in_scope",
        )

    def test_json_cli_outputs_parseable_report(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "saturnum.py"), "status", "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertIn(result.returncode, {0, 1})
        report = json.loads(result.stdout)
        self.assertEqual(report["project"], "Saturnum")
        self.assertIn("checks", report)


if __name__ == "__main__":
    unittest.main()
