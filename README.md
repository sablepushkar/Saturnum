# Saturnum

[![Checks](https://github.com/sablepushkar/Saturnum/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sablepushkar/Saturnum/actions/workflows/ci.yml)

Saturnum is the workspace where I keep two related projects together: Acoustic-B-Box and VIREON. I wanted one place to run their checks while keeping their code and purpose separate.

- **Acoustic-B-Box** explores structured event messages, simulated delivery states and optional audio transport.
- **VIREON** uses synthetic pharmaceutical-style events to test deterministic rules, evidence references and local review workflows.

These components are not connected through one shared production pipeline. Saturnum provides common commands and a combined CI workflow; it does not automatically synchronise the standalone repositories with the copies stored here.

## Structure

```text
components/
  acoustic_bbox/
  vireon/
saturnum.py
tests/
docs/
.github/workflows/ci.yml
```

## First run

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e './components/vireon[test]'
python saturnum.py status
```

## Useful commands

```bash
python saturnum.py status --json
python saturnum.py check
python saturnum.py acoustic --test
python saturnum.py vireon simulate --scenario biomarker-signal
python saturnum.py vireon registry list
python saturnum.py vireon-api
```

The status command checks expected source/test locations and whether key dependencies can be found. It does not run the test suites or check audio hardware. `check` runs the component test suites. The API command starts a local VIREON API; open `http://127.0.0.1:8000/docs` after it starts. See the [portfolio demo guide](docs/portfolio-demo.md) and [project runbook](docs/project-runbook.md).

## Limits

The examples use synthetic data and local storage. Real acoustic delivery between physical devices has not been established by the combined repository checks. The components remain separate, and passing tests do not make either project clinically validated or production-ready. Do not use real patient data or rely on these projects for emergency communication.
