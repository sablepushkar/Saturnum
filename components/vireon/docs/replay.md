# Re-running VIREON signals

VIREON uses deterministic threshold rules. A call without an explicit evaluation time uses the current UTC time, so the timestamp can differ between runs.

For a repeatable test, pass the same synthetic events, thresholds, detector version and timezone-aware evaluated_at value. The resulting signal objects can then be compared between runs.

This checks whether the software behaves consistently for the supplied inputs. It does not show that the rule thresholds are scientifically or clinically correct.
