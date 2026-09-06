from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Evidence:
    kind: str
    domain: str
    payload: dict[str, Any]
    context: str = ""
    source: str = "local"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(slots=True)
class PreferenceWeight:
    domain: str
    feature: str
    weight: float
    updates: int
    updated_at: str

    @property
    def confidence(self) -> float:
        # Evidence-count confidence. Deliberately conservative and interpretable.
        # 1 observation ~= .18, 5 ~= .63, 10 ~= .86, 20 ~= .98.
        import math

        return 1.0 - math.exp(-self.updates / 5.0)


@dataclass(slots=True)
class RankedCandidate:
    text: str
    score: float
    features: dict[str, float]
    contributions: dict[str, float]
