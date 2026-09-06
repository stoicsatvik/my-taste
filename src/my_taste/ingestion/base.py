from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class IngestedAsset:
    modality: str
    uri: str
    metadata: dict[str, object]


class AssetIngestor(Protocol):
    """Adapter contract for future screenshot/image/audio/video ingestion."""

    def ingest(self, path: str | Path) -> IngestedAsset: ...
