# Project VIREON Advanced

**Pharmaceutical Lifecycle Intelligence Engine**

Project VIREON Advanced is my student-built research and engineering prototype for connecting pharmaceutical event data, deterministic review signals, evidence provenance, audit records, and synthetic lifecycle workflows. The core question is practical: can someone reproduce a signal and trace it back to the input that triggered it?

## What currently works

- Validated pharmaceutical event objects and deterministic threshold rules.
- SQLite persistence for the local prototype.
- Evidence references/graph and audit records.
- Data/model registry and evidence manifests.
- Distribution checks, digital-measure validation, and trial-site integrity indicators.
- Synthetic lifecycle scenarios, CLI, FastAPI endpoints, and a small browser dashboard.
- Regression tests for invalid numeric values and thresholds.
- Optional timezone-aware evaluation timestamps so a fixed input/rule/time combination produces repeatable Signal objects.

## Main flow

```text
Synthetic event
      ↓
Domain validation
      ↓
Versioned threshold rules
      ↓
Signal + source event reference
      ↓
Persistence / audit / evidence manifest
      ↓
Human review in API or dashboard
```

The components are deterministic at this stage. The system does not need an opaque model call to explain why a rule fired.

## Quick start

Requires Python 3.11+.

```bash
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
vireon simulate --scenario biomarker-signal
vireon registry list
uvicorn vireon.api:app --reload
```

Then open `http://127.0.0.1:8000/docs` or the local `/dashboard` route. See `docs/demo.md` for the current workflow and `docs/replay.md` for repeatable rule evaluation.

## What the Advanced update adds

A signal's detection time normally reflects the current invocation. For repeatable tests and comparisons, callers can now supply an explicit timezone-aware `evaluated_at` timestamp. This avoids timestamp differences making otherwise identical results appear different during replay. Naive timestamps are rejected rather than interpreted using the machine's local timezone.

Example:

```python
from datetime import datetime, timezone
from vireon.signal_engine import detect_signals

signals = detect_signals(events, evaluated_at=datetime(2026, 10, 10, tzinfo=timezone.utc))
```

## Boundaries

VIREON uses synthetic data and local prototype infrastructure. It does not diagnose, recommend treatment, make autonomous clinical decisions, predict regulatory approval, or claim regulatory compliance. Trial-integrity and monitoring outputs are software review flags, not proof of misconduct or clinical validity. Do not use real patient data.

## Practical next steps

1. Keep API validation and error behavior covered by regression tests.
2. Add stable machine-readable evaluation fixtures for every signal type.
3. Record rule versions and evidence references consistently through historical replay.
4. Keep interoperability mappings explicit about unmapped fields and terminology gaps.
5. Add deployment and observability only after the local workflow is reliable.

See `DEVELOPERS_NOTES.md` for the implementation notes and checks.
