# Acoustic-B-Box — development notes

## Packet validation

The WAV decoder and payload builder need to agree on the internal payload identifier. The validator checks the decoded envelope, required fields and payload size before the packet is accepted.

The tests cover current and invalid packets, missing identifiers, malformed values and oversized packets. These are software checks; they do not establish real acoustic delivery between physical devices.
