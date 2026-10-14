# Project VIREON

VIREON is a student project I use to explore how pharmaceutical-style event data can be checked with simple rules and then traced through a local workflow. The examples are synthetic. I built it to practise Python, data validation, APIs, persistence and repeatable testing—not to make claims about a real pharmaceutical system.

## What is in the project

- Validated event objects and deterministic threshold rules.
- Local SQLite storage for the prototype.
- Evidence references and audit-style records.
- A small registry for data, models and detector versions.
- Synthetic lifecycle scenarios.
- Command-line commands, a FastAPI API and a basic browser dashboard.
- Tests for validation and repeatable signal evaluation.

## How it works

~~~text
Synthetic event
      ↓
Input validation
      ↓
Configured rules
      ↓
Signal with a reference to its source event
      ↓
Local storage, evidence references and review
~~~

A rule-based signal can be explained by looking at the input and the configured threshold. The project does not need a model to make those rule decisions.

## Run it locally

Python 3.11 or newer is recommended.

~~~bash
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
vireon simulate --scenario biomarker-signal
vireon registry list
uvicorn vireon.api:app --reload
~~~

Then open http://127.0.0.1:8000/docs or the local /dashboard route. See docs/demo.md for a short walkthrough.

For repeatable signal evaluation, I can pass an explicit timezone-aware evaluated_at timestamp. The same event, rules and timestamp should produce repeatable results.

## Current limits

VIREON uses synthetic data and local prototype infrastructure. It does not diagnose, recommend treatment, make clinical decisions, predict regulatory approval or establish regulatory compliance. A trial-integrity or monitoring flag is only a software-generated signal; it is not proof of misconduct. Do not use real patient data.

I am keeping the project small and testing its current behaviour before adding more services or machine-learning features. The source code and tests are the best place to check exactly what is implemented.
