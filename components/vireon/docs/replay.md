# Replaying VIREON signal rules

VIREON uses deterministic threshold rules. A normal `detect_signals(...)` call stamps the generated signals with the current UTC time. For regression comparisons or historical replays, pass an explicit timezone-aware timestamp:

```python
from datetime import datetime, timezone
from vireon.signal_engine import detect_signals

replay_time = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
first = detect_signals(events, biomarker_x_threshold=130, evaluated_at=replay_time)
second = detect_signals(events, biomarker_x_threshold=130, evaluated_at=replay_time)
assert first == second
```

A replay is comparable only when the event inputs, thresholds, detector version, and evaluation timestamp are the same. Use synthetic fixtures in tests. This mechanism supports software reproducibility; it does not establish clinical validity or regulatory compliance.
