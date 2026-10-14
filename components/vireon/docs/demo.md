# VIREON Demo

This is the small walkthrough I use to show how the current project fits together.

Everything in the demo is synthetic.

## Start

Install:
python -m pip install -e ".[test]"

Run:
uvicorn vireon.api:app --reload

Open:
http://127.0.0.1:8000/docs

## Walkthrough

### 1. Create an event

Send a synthetic lab result with biomarker_x = 135.

### 2. Detect signals

Call:

POST /v1/signals/detect

The current demonstration rule creates a versioned signal for biomarker_x >= 130.

### 3. Follow the provenance

Call:

GET /v1/signals/SIG-E-DEMO-001

then:

GET /v1/signals/SIG-E-DEMO-001/evidence

and:

GET /v1/evidence/graph

The important part is being able to move from the signal back to the event that produced it.

### 4. Inspect the audit trail

Call:

GET /v1/audit

You should see the event, signal, and evidence operations represented as audit records.

### 5. Run AI-GUARD

Use reference values such as [100, 100, 100] and current values such as [130, 130, 130].

The prototype should report a distribution shift for review.

### 6. Check a digital measure

Send a list containing a few null values to:

POST /v1/digital-measures/validate

This demonstrates missingness monitoring.

### 7. Check trial integrity

Send synthetic site events to:

POST /v1/trial-integrity/sites/{site_id}/assess

Include a protocol deviation or incomplete record to see a review flag.

### 8. View the lifecycle

Call:

GET /v1/lifecycle/CAND-001

The response shows the eight lifecycle stages used by the current simulation.

## What I would explain in a project discussion

The main point is not that these demo rules are clinically sophisticated.

The point is that the project has explicit boundaries:

- synthetic input;
- deterministic analytical logic;
- persisted provenance;
- audit records;
- review flags;
- replaceable interoperability adapters;
- no autonomous clinical decisions.

That gives a clean base for the next engineering layer.
