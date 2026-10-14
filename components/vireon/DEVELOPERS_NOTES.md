# VIREON — development notes

## Making signal evaluation repeatable

Previously, the signal detector generated its timestamp during each call. That meant two runs with the same synthetic event could still produce different full Signal objects.

I added an optional evaluated_at argument to detect_signals. If I do not provide one, it still uses the current UTC time. If I do provide one, it must include a timezone. This avoids silently treating a local, timezone-free timestamp as UTC.

I added tests that run the same event with the same explicit time and compare the resulting signals. The existing rule logic and default thresholds were left unchanged.

## Check it

~~~bash
python -m unittest discover -s tests -v
~~~

For a repeatable run, the event data, thresholds, detector version and timestamp need to be the same. This makes the software easier to test; it does not validate the whole project for real pharmaceutical use.

## Next thing to improve

I want to add a small set of versioned scenarios with expected signals and evidence references, then test them. That seems more useful than adding more dashboard indicators before I know the current ones behave consistently.
