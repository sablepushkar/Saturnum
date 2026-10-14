from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
import json
from typing import Any


class RegistryStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class RegistryItem:
    item_id: str
    version: str
    kind: str
    owner: str
    status: RegistryStatus
    context_of_use: str
    risk_tier: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class Registry:
    def __init__(self, path: str | Path = "vireon-registry.json") -> None:
        self.path = Path(path)

    def list(self) -> list[RegistryItem]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text())
        return [RegistryItem(**{**item, "status": RegistryStatus(item["status"])}) for item in raw]

    def upsert(self, item: RegistryItem) -> None:
        items = {x.item_id: x for x in self.list()}
        items[item.item_id] = item
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([x.as_dict() for x in items.values()], indent=2, sort_keys=True) + "\n")
