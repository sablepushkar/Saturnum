# Acoustic-B-Box — A.B.B Q3

Acoustic-B-Box is my experiment with moving a structured event through a simple delivery workflow. It currently has a software simulator and an optional GGWave-based WAV encode/decode path.

## What I have built

- Synthetic event types with P0–P4 priority labels.
- Department and role routing fields with lifecycle transitions.
- SQLite storage for events, transmission attempts, device-status examples and audit entries.
- Retry/failure simulation and event timelines.
- A SHA-256 fingerprint of the canonical payload.
- A terminal dashboard, demo scenarios and a hardware-free self-test.
- Optional audio encoding/decoding and automated tests.

The device counts in the dashboard are seeded simulator data, not live availability.

## Run it

~~~bash
python acoustic_bbox.py --test
python acoustic_bbox.py --demo
python acoustic_bbox.py --dashboard
python acoustic_bbox.py --simulate
~~~

To inspect an event timeline:

~~~bash
python acoustic_bbox.py --timeline BX-XXXXXXXX
~~~

For the optional WAV path:

~~~bash
python -m pip install -r requirements.txt
python acoustic_bbox.py --encode-wav BX-XXXXXXXX --wav-out acoustic_event.wav
python acoustic_bbox.py --decode-wav acoustic_event.wav
~~~

## Q3 change

I found that the WAV decoder was still checking an old version string. I updated it to use the same version as the payload builder and added a separate packet validator. This lets me test current and malformed packets without connecting audio hardware.

## What is still untested

A passing simulator run does not prove real acoustic delivery. I have not established the usable range, reliability under interference, privacy or successful delivery between physical devices. The hash detects changes to a payload but does not authenticate a sender.

This is a learning prototype, not an emergency dispatch product or medical device. Use synthetic data only, and do not rely on it for real emergencies.

The project is also included in Saturnum, where I run combined checks with VIREON.
