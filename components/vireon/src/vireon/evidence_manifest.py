from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class EvidenceManifest:
    manifest_id: str
    generated_at: str
    dataset: str
    detector_version: str
    input_ids: list[str]
    signal_ids: list[str]
    evidence_ids: list[str]
    content_fingerprint: str = ""
    review_status: str = "pending"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_manifest(
    dataset: str,
    detector_version: str,
    input_ids: Sequence[str],
    signal_ids: Sequence[str],
    evidence_ids: Sequence[str],
    review_status: str = "pending",
    content_fingerprint: str = "",
) -> EvidenceManifest:
    payload = {
        "dataset": dataset,
        "detector_version": detector_version,
        "input_ids": list(input_ids),
        "signal_ids": list(signal_ids),
        "evidence_ids": list(evidence_ids),
        "review_status": review_status,
        "content_fingerprint": content_fingerprint,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    manifest_id = "MAN-" + sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return EvidenceManifest(
        manifest_id=manifest_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        dataset=dataset,
        detector_version=detector_version,
        input_ids=list(input_ids),
        signal_ids=list(signal_ids),
        evidence_ids=list(evidence_ids),
        content_fingerprint=content_fingerprint,
        review_status=review_status,
    )


def serialize_manifest(manifest: EvidenceManifest) -> str:
    return json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n"
