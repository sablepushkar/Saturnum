from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .core.models import EvidenceLink, PharmaEvent, Signal

@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    node_type: str
    label: str

@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    relationship: str

class EvidenceGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: set[GraphEdge] = set()
    def add_event(self, event: PharmaEvent) -> None:
        self.nodes[event.event_id] = GraphNode(event.event_id, "event", event.event_type.value)
    def add_signal(self, signal: Signal) -> None:
        self.nodes[signal.signal_id] = GraphNode(signal.signal_id, "signal", signal.signal_type)
        self.edges.add(GraphEdge(signal.event_id, signal.signal_id, "produced_signal"))
    def add_evidence(self, evidence: EvidenceLink) -> None:
        self.nodes[evidence.evidence_id] = GraphNode(evidence.evidence_id, "evidence", evidence.relationship)
        self.edges.add(GraphEdge(evidence.signal_id, evidence.evidence_id, "supported_by"))
    def as_dict(self) -> dict[str, object]:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "nodes": [{"id": n.node_id, "type": n.node_type, "label": n.label} for n in self.nodes.values()],
            "edges": [{"source": e.source, "target": e.target, "relationship": e.relationship}
                      for e in sorted(self.edges, key=lambda x: (x.source, x.target, x.relationship))],
        }
