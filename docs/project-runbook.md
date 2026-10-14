# Project runbook

This file is my quick reference for running the prototypes. Saturnum contains copies of Acoustic-B-Box and VIREON under `components/`. Those copies are separate from the standalone GitHub repositories, so a change in one repository does not automatically update the other.

## Before running

Use Python 3.11 or newer. From the Saturnum repository root, install VIREON and its test dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e './components/vireon[test]'
```

If you want to test the optional audio path, install the packages listed in `components/acoustic_bbox/requirements.txt` on a device where the audio dependencies are supported. The unit tests and simulator do not prove that two physical devices can exchange audio reliably.

## Saturnum workspace

```bash
python saturnum.py status
python saturnum.py status --json
python saturnum.py check
```

`status` checks that source folders and core VIREON dependencies are available. It does not run a hardware test. `check` runs the Acoustic-B-Box and VIREON unit-test suites.

## Acoustic-B-Box

```bash
python saturnum.py acoustic --test
python saturnum.py acoustic --help
```

The project creates structured event envelopes, validates fields, records simulated delivery states and stores a local SQLite timeline. The optional WAV/ggwave path is an experiment. A passing simulated retry test is not proof of real-world audio delivery, sender identity, or emergency-response suitability. The SHA-256 value checks payload consistency; it is not authentication.

## VIREON

```bash
python saturnum.py vireon simulate --scenario biomarker-signal
python saturnum.py vireon registry list
python saturnum.py vireon --help
```

VIREON accepts synthetic events, validates their structure, stores events and signals in SQLite, applies deterministic threshold rules and connects results to evidence records. The API can be started locally with `python saturnum.py vireon-api`; use the API's local docs page to inspect available routes.

## Standalone repositories

- Acoustic-B-Box has its own README and tests in its own repository.
- VIREON has its own README, `pyproject.toml` and tests in its own repository.
- MedFindr is a separate Streamlit application and is not part of Saturnum's command runner.
- Consulting Analytics Lab is a separate Python project with its own tests and data scripts.

## How I check a change

1. Read the relevant code and tests before editing.
2. Run the narrow test for the changed behavior.
3. Run the full component tests or the repository's full CI workflow.
4. Check the latest GitHub Actions result on the commit.
5. Keep unverified hardware behavior, external-service behavior and domain accuracy listed as limitations.
