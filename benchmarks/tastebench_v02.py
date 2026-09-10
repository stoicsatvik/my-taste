from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

from my_taste.core.context_engine import ContextTasteEngine
from my_taste.core.engine import TasteEngine

# Synthetic, preregistered context-conflict fixture. Training and holdout wording are
# disjoint; both models receive the exact same pairwise evidence in the same order.
TRAIN = [
    ("chat", "Short answer.", "We leverage innovative robust solutions to transform the ecosystem."),
    ("chat", "Keep it brief!", "Our cutting-edge dynamic ecosystem unlocks seamless transformation."),
    ("proposal", "Our innovative robust solutions transform the dynamic ecosystem.", "Short answer."),
    ("proposal", "Leverage cutting-edge solutions to optimize the ecosystem.", "Keep it brief!"),
]

HOLDOUT = [
    ("chat", "Direct reply.", "We empower a next-generation ecosystem with seamless innovative solutions."),
    ("chat", "Concise response.", "Our robust dynamic solutions revolutionize the ecosystem."),
    ("proposal", "A robust innovative ecosystem can unlock dynamic solutions.", "Direct reply."),
    ("proposal", "Optimize the next-generation ecosystem with cutting-edge solutions.", "Concise response."),
]


def pair_probability(engine: TasteEngine, preferred: str, rejected: str, context: str | None = None) -> float:
    if isinstance(engine, ContextTasteEngine):
        ranked = engine.rank_text([preferred, rejected], context=context or "")
    else:
        ranked = engine.rank_text([preferred, rejected])
    scores = {item.text: item.score for item in ranked}
    return engine._sigmoid(scores[preferred] - scores[rejected])


def evaluate(engine: TasteEngine, contextual: bool) -> dict[str, float]:
    probs = [pair_probability(engine, p, r, c if contextual else None) for c, p, r in HOLDOUT]
    accuracy = sum(p > 0.5 for p in probs) / len(probs)
    brier = sum((1.0 - p) ** 2 for p in probs) / len(probs)
    return {"accuracy": accuracy, "brier": brier, "mean_probability": sum(probs) / len(probs)}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        baseline = TasteEngine(root / "v01.sqlite")
        challenger = ContextTasteEngine(root / "v02.sqlite")
        for context, preferred, rejected in TRAIN:
            baseline.observe_choice(preferred, rejected, context=context)
            challenger.observe_choice(preferred, rejected, context=context)

        base = evaluate(baseline, contextual=False)
        v02 = evaluate(challenger, contextual=True)
        result = {
            "fixture": "synthetic-context-conflict-v1",
            "train_pairs_per_model": len(TRAIN),
            "holdout_pairs": len(HOLDOUT),
            "v01": base,
            "v02_contextual": v02,
        }
        print(json.dumps(result, sort_keys=True))

        # Promotion gate is intentionally strict on this synthetic fixture: context
        # must improve discrimination and calibration under the matched evidence budget.
        assert v02["accuracy"] > base["accuracy"], result
        assert v02["brier"] < base["brier"], result
        assert math.isfinite(v02["brier"]), result


if __name__ == "__main__":
    main()
