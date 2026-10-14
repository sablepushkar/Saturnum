# Acoustic-B-Box — A.B.B Q3

**A small event-communication and delivery-audit prototype**

Acoustic-B-Box models how a structured operational event can move through validation, payload encoding, transport attempts, acknowledgement, work-in-progress, and resolution. Q3 focuses on keeping the versioned message envelope consistent across the simulator and the optional acoustic WAV decoder.

## What works in the prototype

- Synthetic event categories and P0–P4 priority labels.
- Department/role routing fields and explicit lifecycle transitions.
- SQLite storage for events, transmissions, device status, and audit entries.
- Retry/failure simulation and per-event timeline.
- SHA-256 fingerprint of the canonical payload.
- Terminal dashboard, demo scenarios, and hardware-free self-test. Device counts are seeded simulator rows, not live availability checks.
- Optional GGWave WAV encode/decode path.
- Automated tests and GitHub Actions checks.

## Event path

```text
Create event → validate → canonical payload/hash → transport attempt
      → delivery/failure → acknowledgement → work → resolution
      → persisted event, transmission history, and audit trail
```

## Run it

The core simulator uses the Python standard library:

```bash
python acoustic_bbox.py --test
python acoustic_bbox.py --demo
python acoustic_bbox.py --dashboard
python acoustic_bbox.py --simulate
```

Inspect an event timeline with its event ID:

```bash
python acoustic_bbox.py --timeline BX-XXXXXXXX
```

For the optional audio experiment:

```bash
python -m pip install -r requirements.txt
python acoustic_bbox.py --encode-wav BX-XXXXXXXX --wav-out acoustic_event.wav
python acoustic_bbox.py --decode-wav acoustic_event.wav
```

## Q3 — what changed

- The project and outgoing payload now use the `A.B.B Q3` version label.
- The WAV decoder now validates against the current project version rather than the old `0.3` string. This fixes a stale version check that would reject packets created by the current payload builder.
- The decoded envelope validation is a separate function, so version, message-ID, and basic packet-shape behavior can be tested without requiring acoustic hardware or the optional GGWave dependency.
- Regression tests cover the current version and stale/malformed packet envelopes.

## Limits that matter

All examples are synthetic. This is not an emergency dispatch product, medical device, or reliable alert channel. A successful simulator run does not establish acoustic range, intelligibility, privacy, interference tolerance, or delivery guarantees on real hardware. The physical audio path still needs controlled testing on actual devices before any operational claim could be made. Do not use real patient data or rely on this for real emergency response.

## Next practical steps

1. Run the complete self-test and automated test suite after each transport change.
2. Add repeated-run delivery metrics for the simulator with clearly stated test conditions.
3. Test audio round trips and failure rates on actual hardware before making performance claims.
4. Add identity, authorization, and threat modelling before considering networked deployment.

See `DEV_NOTES.md` and `docs/transport-validation.md` for the current transport contract and limits.
