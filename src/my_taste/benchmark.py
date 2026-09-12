from __future__ import annotations

from dataclasses import dataclass
from math import fsum
from pathlib import Path
from tempfile import TemporaryDirectory

from .core.engine import TasteEngine


@dataclass(frozen=True)
class Pair:
    preferred: str
    rejected: str
    context: str


def brier(probabilities: list[float]) -> float:
    return fsum((1.0 - p) ** 2 for p in probabilities) / len(probabilities)


def evaluate(engine: TasteEngine, pairs: list[Pair], *, use_context: bool) -> dict[str, float]:
    probabilities = [
        engine.pairwise_probability(p.preferred, p.rejected, context=p.context if use_context else "")
        for p in pairs
    ]
    return {
        "accuracy": sum(p > 0.5 for p in probabilities) / len(probabilities),
        "brier": brier(probabilities),
    }


def synthetic_context_benchmark() -> dict[str, dict[str, float]]:
    # Synthetic fixture deliberately creates context-dependent choices. No user evidence.
    concise = "Revenue rose 18% after checkout dropped from four steps to two."
    expansive = "We leverage innovative seamless solutions to transform a dynamic ecosystem with comprehensive strategic capabilities."
    train = [
        Pair(concise, expansive, "status update"),
        Pair(concise, expansive, "status update"),
        Pair(expansive, concise, "ceremonial speech"),
        Pair(expansive, concise, "ceremonial speech"),
    ]
    held_out = [
        Pair(concise, expansive, "status update"),
        Pair(expansive, concise, "ceremonial speech"),
    ]
    with TemporaryDirectory() as directory:
        engine = TasteEngine(Path(directory) / "taste.db")
        for pair in train:
            engine.observe_choice(pair.preferred, pair.rejected, context=pair.context)
        return {
            "v0_1_no_context": evaluate(engine, held_out, use_context=False),
            "v0_2_context": evaluate(engine, held_out, use_context=True),
        }
