# Acoustic-B-Box — Developer Notes

## A.B.B Q3 — version-consistent transport envelope

While rechecking the previous update, I found a stale check in the optional WAV decoder: it still expected payload version `0.3`, even though the payload builder had already moved to the named project version. That meant a current payload could be rejected by the decoder. Q3 fixes that mismatch and makes the envelope check directly testable.

### What changed

- Set the project/payload version to `A.B.B Q3`.
- Added `validate_decoded_packet` to check that a decoded envelope is a JSON object, uses the current version, and has a non-empty message ID.
- Routed the WAV decoder through that validator.
- Added regression tests for current, stale, missing-ID, and non-object packets.
- Kept the simulator and optional GGWave dependency boundaries unchanged.

### Check it

```bash
python acoustic_bbox.py --test
python -m unittest discover -s tests -v
```

The decoder contract can be tested without installing GGWave. A real acoustic round trip still requires the optional dependency and controlled audio testing.

### Limits

The simulator is not proof of real-world delivery reliability. The payload hash detects content changes but does not authenticate a sender. All medical-style examples remain synthetic; this is not an emergency response or medical device.
