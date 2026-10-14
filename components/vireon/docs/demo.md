# VIREON demo

This is the short local walkthrough I use to check the main path. All data in the demo is synthetic.

## Start

~~~bash
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
vireon simulate --scenario biomarker-signal
vireon registry list
uvicorn vireon.api:app --reload
~~~

Open http://127.0.0.1:8000/docs for the API documentation or visit /dashboard on the local server.

## What to look for

1. The scenario creates example event data.
2. The input is checked before the rules run.
3. The detector produces signals based on the configured thresholds.
4. Results can be saved locally and linked to their source event.
5. The registry command shows the metadata available in the local prototype.

A successful demo only shows that this example path runs in the current environment. It does not show that the rules are suitable for a real pharmaceutical workflow.
