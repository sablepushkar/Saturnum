# Checks I run in Saturnum

Saturnum is a shared workspace and command entry point. It does not combine Acoustic-B-Box and VIREON into one end-to-end service.

## Quick status check

~~~bash
python saturnum.py status
python saturnum.py status --json
~~~

This checks whether the expected source and test paths exist and whether FastAPI and Uvicorn can be found in the current Python environment. It also reports whether optional audio packages are installed. That does not prove audio transmission works.

## Run the tests

~~~bash
python saturnum.py check
python saturnum.py acoustic --test
python saturnum.py vireon simulate --scenario biomarker-signal
python saturnum.py vireon registry list
~~~

GitHub Actions compiles the code, runs the status-report tests, checks the JSON report, runs both component test suites, runs the Acoustic-B-Box software self-test and runs a couple of VIREON CLI commands.

A green workflow means those checks passed in that CI environment for that commit. It does not mean every possible input or real device setup has been tested.

## Gaps I know about

- The status report is not a running-service health check.
- The components use synthetic or local examples.
- Real acoustic transmission between physical devices has not been verified here.
- There is no shared production event pipeline between the components.
- These checks do not establish clinical validity, deployment security or sender authentication.
