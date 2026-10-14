# Project VIREON Advanced — Developer Notes

## Advanced update — reproducible signal evaluation

The previous signal engine validated thresholds and handled extreme numeric inputs, but the timestamp was always generated inside the detector. That made two otherwise identical calls produce different full Signal objects.

### What changed

- Added an optional `evaluated_at` argument to `detect_signals`.
- Kept the current UTC timestamp as the default for normal use.
- Require an explicit timestamp to be timezone-aware.
- Added tests that run the same synthetic event twice at the same timestamp and compare the resulting Signal objects.
- Kept the existing rule logic and default thresholds intact.

### Check it

```bash
python -m unittest discover -s tests -v
```

For a reproducible run, pass the same event data, thresholds, detector version, and timezone-aware `evaluated_at` value. This improves replayability; it is not a claim that the overall system is validated or production-ready.

### Next practical work

The next worthwhile milestone is a versioned scenario fixture with expected signals and evidence references. That should come before adding machine learning or expanding the number of dashboard indicators.
