# Acoustic-B-Box — development notes

## Q3: packet version consistency

While checking the WAV decoder, I found that it still expected payload version 0.3, while the builder was using the named project version. I fixed the mismatch and moved the envelope check into validate_decoded_packet.

The function checks that the decoded packet is a JSON object, uses the current version and has a non-empty message ID. I added tests for a current packet, an old version, a missing ID and a non-object value.

## Commands I use

~~~bash
python acoustic_bbox.py --test
python -m unittest discover -s tests -v
~~~

These checks do not require GGWave or audio hardware. A real round trip still needs controlled testing on physical devices. The simulator is not proof of delivery reliability, and the payload hash is not sender authentication.
