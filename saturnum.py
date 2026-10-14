#!/usr/bin/env python3
"""Unified command entry point for Saturnum's independent components."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

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

def main() -> int:
    parser = argparse.ArgumentParser(description="Saturnum unified prototype runner")
    sub = parser.add_subparsers(dest="component", required=True)
    sub.add_parser("check", help="run both components' unit-test suites")
    acoustic = sub.add_parser("acoustic", help="run the Acoustic-B-Box command")
    acoustic.add_argument("args", nargs=argparse.REMAINDER)
    vireon = sub.add_parser("vireon", help="run VIREON's CLI")
    vireon.add_argument("args", nargs=argparse.REMAINDER)
    sub.add_parser("vireon-api", help="start VIREON's local FastAPI development server")
    args, passthrough = parser.parse_known_args()

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
