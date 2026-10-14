# A.B.B Q3 transport validation

The payload builder writes the current project version into `bbox_version`. The WAV decoder checks the same version through `validate_decoded_packet` so old or malformed envelopes are rejected consistently.

## Hardware-free checks

```bash
python acoustic_bbox.py --test
python -m unittest discover -s tests -v
```

The tests cover current-version packets, stale versions, missing message identifiers, and non-object JSON values. These checks validate the software envelope contract only; they do not require GGWave or prove acoustic delivery.

## Acoustic experiment

After installing the optional dependency, encode a synthetic event to WAV and decode it again using the commands in the main README. Record the device, sample rate, playback/recording setup, number of attempts, successful decodes, and corrupted-payload rejections. Do not report simulator outcomes as acoustic results.

SHA-256 is used as a payload fingerprint. It is not sender authentication or encryption. Do not use this prototype for real emergency communication or real patient information.
