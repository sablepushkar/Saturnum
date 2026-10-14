from __future__ import annotations

import argparse
import json

from . import __version__
from .scenarios import SCENARIOS, run_scenario
from .registry import Registry


def main() -> int:
    parser = argparse.ArgumentParser(prog="vireon", description="VIREON portfolio CLI")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate", help="run a deterministic synthetic scenario")
    sim.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal-trial")
    sim.add_argument("--seed", type=int, default=42)

    reg = sub.add_parser("registry", help="inspect the local model/data registry")
    reg.add_argument("action", choices=["list"])

    args = parser.parse_args()
    if args.command == "simulate":
        print(json.dumps(run_scenario(args.scenario, args.seed).as_dict(), indent=2))
        return 0
    if args.command == "registry":
        print(json.dumps([x.as_dict() for x in Registry().list()], indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
