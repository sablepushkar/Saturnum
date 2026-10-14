# Acoustic-B-Box transport checks

The payload builder writes the project version into bbox_version. The WAV decoder checks it through validate_decoded_packet, so old or malformed envelopes can be rejected consistently.

## Software checks

~~~bash
python acoustic_bbox.py --test
python -m unittest discover -s tests -v
~~~

These tests cover packet shape, version and message ID. They do not need GGWave and do not prove that audio transmission works.

## Physical test notes

If I run the optional audio experiment, I should record the device, sample rate, playback/recording setup, number of attempts, successful decodes and rejected packets. Results from the simulator must not be counted as audio results.

SHA-256 is only a payload fingerprint. It does not encrypt the message or prove who sent it. Do not use this prototype for real emergencies or real patient data.
