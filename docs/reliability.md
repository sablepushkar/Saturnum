# Saturnum reliability and observability notes

Saturnum keeps Acoustic-B-Box and VIREON as separate components. The shared command entry point is an operator convenience, not a shared end-to-end data pipeline.

## Local preflight report

~~~bash
python saturnum.py status
python saturnum.py status --json
~~~

The report records the Python version, checks that the expected source and test locations exist, and checks that FastAPI and Uvicorn are discoverable for VIREON's API entry point. The JSON shape is versioned with the report_schema_version field. Optional GGWave and sounddevice dependency presence is reported separately and does not imply successful audio transmission.

## Automated checks

~~~bash
python saturnum.py check
python saturnum.py acoustic --test
python saturnum.py vireon simulate --scenario biomarker-signal
python saturnum.py vireon registry list
~~~

GitHub Actions runs compilation, Saturnum-level status/report tests, both component test suites, the Acoustic-B-Box hardware-free self-test, and VIREON CLI smoke checks. A passing workflow demonstrates only that these automated checks passed for that commit and environment.

## Known boundaries

- The status report is a preflight, not a health check of a running service and not a test runner.
- Component tests use synthetic/local examples; they do not validate a real pharmaceutical workflow.
- The Acoustic-B-Box physical audio round trip remains unverified in this repository integration. Hardware, room, device, and sample-rate conditions need a separately recorded experiment.
- VIREON and Acoustic-B-Box remain separate components; no production-grade cross-component event pipeline is claimed.
- No patient data, clinical validation, sender authentication, or deployment-grade security is implied by these checks.
