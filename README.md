# Saturnum

**A student-built prototype workspace for event transport, deterministic simulation, and evidence traceability.**

Saturnum brings two existing projects together without blending away their separate responsibilities:

- **Acoustic-B-Box** — structured event messaging, delivery-state simulation, audit trails, and optional acoustic WAV transport experiments.
- **VIREON** — deterministic pharmaceutical lifecycle event simulation, rule-based signals, local persistence, evidence provenance, and review APIs.

## Repository layout

~~~text
components/
  acoustic_bbox/   # Acoustic-B-Box source, tests, and component documentation
  vireon/          # VIREON source, tests, and component documentation
saturnum.py        # Unified command-line entry point and status report
tests/             # Saturnum-level status/report tests
.github/workflows/ci.yml  # Combined CI for both components and the status check
~~~

## Requirements

- Python 3.11 or newer.
- Network access is only needed to install VIREON's Python dependencies.
- Acoustic transport is optional; the simulator and core tests do not require a physical acoustic device.

## Setup

~~~bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e './components/vireon[test]'
~~~

## Run

~~~bash
python saturnum.py status
python saturnum.py status --json
python saturnum.py check
python saturnum.py acoustic --test
python saturnum.py vireon simulate --scenario biomarker-signal
python saturnum.py vireon registry list
~~~

The status command checks that component source/test directories and the declared VIREON API dependencies are present in the current environment. It does not run the unit suites or verify acoustic hardware. Use the check command for the automated component tests.

To start VIREON's local API, run python saturnum.py vireon-api; then open http://127.0.0.1:8000/docs.

Component-specific details and limitations are documented in components/acoustic_bbox/README.md and components/vireon/README.md. The CI checks and known gaps are summarized in docs/reliability.md.

## Boundaries

This is a research and engineering prototype using synthetic examples and local storage. The projects are not clinically validated, do not provide medical advice, and are not production-ready medical or pharmaceutical systems. Acoustic transmission has not been verified on real devices as part of this repository integration. Do not use real patient data.
