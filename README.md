# Saturnum

Saturnum is the workspace where I keep two of my related projects together: Acoustic-B-Box and VIREON. I wanted one place to run their checks while keeping their code and purpose separate.

- Acoustic-B-Box is an experiment with structured event messages, delivery-state simulation and optional audio transport.
- VIREON uses synthetic pharmaceutical-style events to test deterministic rules, evidence references and local review workflows.

The two components are not connected through one shared production pipeline. Saturnum currently gives me a common command line and a combined CI workflow.

## Folder layout

~~~text
components/
  acoustic_bbox/
  vireon/
saturnum.py
tests/
docs/reliability.md
.github/workflows/ci.yml
~~~

## Setup

Python 3.11 or newer is recommended.

~~~bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e './components/vireon[test]'
~~~

## Commands

~~~bash
python saturnum.py status
python saturnum.py status --json
python saturnum.py check
python saturnum.py acoustic --test
python saturnum.py vireon simulate --scenario biomarker-signal
python saturnum.py vireon registry list
~~~

The status command checks expected source and test locations and whether FastAPI and Uvicorn can be found. It does not run the test suites or check audio hardware. The check command runs both component test suites.

To start the local VIREON API, run python saturnum.py vireon-api and open http://127.0.0.1:8000/docs.

## Current limits

The examples use synthetic data and local storage. I have not verified a real acoustic round trip between devices as part of this combined repository. The components remain separate, and passing tests do not make either project a clinically validated or production-ready system. Do not use real patient data or rely on these projects for emergency communication.

See docs/reliability.md and the component READMEs for details.

## Running the workspace

I keep the main commands and what they check in [the project runbook](docs/project-runbook.md).
