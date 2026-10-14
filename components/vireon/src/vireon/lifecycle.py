from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import StrEnum

class LifecycleStage(StrEnum):
    DISCOVERY = "discovery"
    PRECLINICAL = "preclinical"
    PHASE_I = "phase_i"
    PHASE_II = "phase_ii"
    PHASE_III = "phase_iii"
    REGULATORY = "regulatory"
    MANUFACTURING = "manufacturing"
    POST_MARKET = "post_market"

@dataclass(frozen=True, slots=True)
class LifecycleSnapshot:
    candidate_id: str
    stage: LifecycleStage
    risk_flags: tuple[str, ...]
    evidence_count: int
    def as_dict(self) -> dict[str, object]:
        return asdict(self)

def simulate_lifecycle(candidate_id: str) -> list[LifecycleSnapshot]:
    if not candidate_id.strip():
        raise ValueError("candidate_id must not be empty")
    result: list[LifecycleSnapshot] = []
    for index, stage in enumerate(LifecycleStage):
        flags: list[str] = []
        if stage in {LifecycleStage.PHASE_I, LifecycleStage.PHASE_II}:
            flags.append("requires_human_review")
        if stage == LifecycleStage.POST_MARKET:
            flags.append("pharmacovigilance_monitoring")
        result.append(LifecycleSnapshot(candidate_id, stage, tuple(flags), index))
    return result
