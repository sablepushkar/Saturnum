#!/usr/bin/env python3
"""Unified command entry point and preflight diagnostics for Saturnum's components."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ACOUSTIC = ROOT / "components" / "acoustic_bbox"
VIREON = ROOT / "components" / "vireon"


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
    result = subprocess.run(command, cwd=cwd, env=env, check=False)
    return result.returncode


def _vireon_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(VIREON / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def build_status_report() -> dict[str, Any]:
    """Report local source/dependency readiness without running hardware tests."""
    checks = []
    for name, path, detail in [
        ("acoustic_component_source", ACOUSTIC / "acoustic_bbox.py", "Acoustic-B-Box entry-point file"),
        ("acoustic_component_tests", ACOUSTIC / "tests", "Acoustic-B-Box test directory"),
        ("vireon_source", VIREON / "src" / "vireon" / "__init__.py", "VIREON package source"),
        ("vireon_component_tests", VIREON / "tests", "VIREON test directory"),
    ]:
        present = path.is_file() if path.suffix else path.is_dir()
        checks.append({
            "name": name,
            "status": "pass" if present else "fail",
            "detail": f"{detail} is present." if present else f"{detail} is missing.",
        })

    for module in ("fastapi", "uvicorn"):
        present = _module_available(module)
        checks.append({
            "name": f"vireon_{module}_dependency",
            "status": "pass" if present else "fail",
            "detail": f"{module} is import-discoverable."
            if present else f"{module} is not installed in this Python environment.",
        })

    optional_audio = {
        "ggwave_installed": _module_available("ggwave"),
        "sounddevice_installed": _module_available("sounddevice"),
    }
    return {
        "project": "Saturnum",
        "report_schema_version": 1,
        "python_version": platform.python_version(),
        "overall_status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
        "checks": checks,
        "optional_audio_dependencies": optional_audio,
        "capability_boundaries": {
            "synthetic_component_tests": "run separately with python saturnum.py check",
            "acoustic_hardware_round_trip": "not_tested_by_this_report",
            "clinical_or_pharmaceutical_validation": "not_in_scope",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Saturnum unified prototype runner")
    sub = parser.add_subparsers(dest="component", required=True)
    sub.add_parser("check", help="run both components' unit-test suites")
    status = sub.add_parser("status", help="report source and runtime dependency readiness")
    status.add_argument("--json", action="store_true", help="print a machine-readable JSON report")
    acoustic = sub.add_parser("acoustic", help="run the Acoustic-B-Box command")
    acoustic.add_argument("args", nargs=argparse.REMAINDER)
    vireon = sub.add_parser("vireon", help="run VIREON's CLI")
    vireon.add_argument("args", nargs=argparse.REMAINDER)
    sub.add_parser("vireon-api", help="start VIREON's local FastAPI development server")
    args, passthrough = parser.parse_known_args()

    if args.component == "status":
        if passthrough:
            parser.error(f"unexpected arguments for status: {' '.join(passthrough)}")
        report = build_status_report()
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"Saturnum status: {report['overall_status']}")
            print(f"Python: {report['python_version']}")
            for item in report["checks"]:
                print(f"- {item['status'].upper():4} {item['name']}: {item['detail']}")
            print("Acoustic hardware round-trip: not tested by this status report.")
        return 0 if report["overall_status"] == "pass" else 1

    if args.component == "check":
        if passthrough:
            parser.error(f"unexpected arguments for check: {' '.join(passthrough)}")
        commands = [
            ([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ACOUSTIC, None),
            ([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], VIREON, _vireon_env()),
        ]
        for command, cwd, env in commands:
            if not cwd.is_dir():
                print(f"Missing component directory: {cwd}", file=sys.stderr)
                return 2
            code = _run(command, cwd=cwd, env=env)
            if code:
                return code
        return 0

    if args.component == "acoustic":
        return _run([sys.executable, str(ACOUSTIC / "acoustic_bbox.py"), *args.args, *passthrough], cwd=ACOUSTIC)

    if args.component == "vireon":
        env = _vireon_env()
        return _run([sys.executable, "-c", "from vireon.cli import main; main()", *args.args, *passthrough], cwd=VIREON, env=env)

    if args.component == "vireon-api":
        env = _vireon_env()
        return _run([sys.executable, "-m", "uvicorn", "vireon.api:app", "--reload"], cwd=VIREON, env=env)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
