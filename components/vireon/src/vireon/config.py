from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VireonConfig:
    database_path: Path = Path("vireon.db")
    biomarker_x_threshold: float = 130.0
    heart_rate_threshold: float = 120.0
    max_query_limit: int = 1000
    environment: str = "development"

    def __post_init__(self) -> None:
        for name, value in (("biomarker_x_threshold", self.biomarker_x_threshold), ("heart_rate_threshold", self.heart_rate_threshold)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if isinstance(self.max_query_limit, bool) or not isinstance(self.max_query_limit, int) or not 1 <= self.max_query_limit <= 1000:
            raise ValueError("max_query_limit must be between 1 and 1000")

    @classmethod
    def from_env(cls) -> "VireonConfig":
        return cls(
            database_path=Path(os.getenv("VIREON_DATABASE_PATH", "vireon.db")),
            biomarker_x_threshold=float(os.getenv("VIREON_BIOMARKER_X_THRESHOLD", "130")),
            heart_rate_threshold=float(os.getenv("VIREON_HEART_RATE_THRESHOLD", "120")),
            max_query_limit=int(os.getenv("VIREON_MAX_QUERY_LIMIT", "1000")),
            environment=os.getenv("VIREON_ENVIRONMENT", "development"),
        )


def load_config() -> VireonConfig:
    return VireonConfig.from_env()
