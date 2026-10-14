# Saturnum: portfolio demo

This demo shows Saturnum as a small workspace and test entry point, not as an integrated production service.

## 1. Set up

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e './components/vireon[test]'
```

Activate the environment first when using a virtual environment.

## 2. Show the workspace

```bash
python saturnum.py status
python saturnum.py status --json
python saturnum.py check
```

Keep the terminal output. `status` is an environment/source check; `check` is the command that runs the component tests.

## 3. Run one example from each component

```bash
python saturnum.py acoustic --test
python saturnum.py vireon simulate --scenario biomarker-signal
python saturnum.py vireon registry list
```

Optional local API: `python saturnum.py vireon-api`, then visit `http://127.0.0.1:8000/docs`.

## What this demo establishes

It demonstrates a common command-line entry point, a combined test workflow and access to examples from both components. It does not show a shared end-to-end data pipeline. Standalone component repositories and their copies in Saturnum can differ until changes are deliberately copied across.
