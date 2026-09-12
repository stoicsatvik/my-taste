from __future__ import annotations

import json
import tempfile
from pathlib import Path

from my_taste.core.hierarchical_context_engine import HierarchicalContextTasteEngine

PREFERRED = "Short direct answer."
REJECTED = "We leverage innovative robust solutions to transform the dynamic ecosystem."
TRAIN_CONTEXT = "work-email"
RELATED_CONTEXT = "work-memo"
UNRELATED_CONTEXT = "casual-chat"
FAMILIES = {TRAIN_CONTEXT: "work", RELATED_CONTEXT: "work", UNRELATED_CONTEXT: "casual"}
OBSERVATIONS = 8
REVERSALS = 8
TRANSFER_MIN = 0.60
UNRELATED_DRIFT_MAX = 1e-12
FAMILY_SHARE = 0.35
CONTEXT_RETENTION = 0.75


def probability(engine, preferred: str, rejected: str, context: str) -> float:
    ranked = engine.rank_text([preferred, rejected], context=context)
    scores = {item.text: item.score for item in ranked}
    return engine._sigmoid(scores[preferred] - scores[rejected])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = HierarchicalContextTasteEngine(
            Path(tmp) / "hierarchical.sqlite",
            context_families=FAMILIES,
            family_share=FAMILY_SHARE,
            context_retention=CONTEXT_RETENTION,
        )
        related_before = probability(engine, PREFERRED, REJECTED, RELATED_CONTEXT)
        unrelated_before = probability(engine, PREFERRED, REJECTED, UNRELATED_CONTEXT)
        for _ in range(OBSERVATIONS):
            engine.observe_choice(PREFERRED, REJECTED, context=TRAIN_CONTEXT)
        trained_after = probability(engine, PREFERRED, REJECTED, TRAIN_CONTEXT)
        related_after = probability(engine, PREFERRED, REJECTED, RELATED_CONTEXT)
        unrelated_after_training = probability(engine, PREFERRED, REJECTED, UNRELATED_CONTEXT)
        for _ in range(REVERSALS):
            engine.observe_choice(REJECTED, PREFERRED, context=TRAIN_CONTEXT)
        reversed_after = probability(engine, REJECTED, PREFERRED, TRAIN_CONTEXT)
        unrelated_after_reversal = probability(engine, PREFERRED, REJECTED, UNRELATED_CONTEXT)
        result = {
            "fixture": "synthetic-hierarchical-transfer-v1",
            "challenger": "explicit-family-hierarchy-v1",
            "family_share": FAMILY_SHARE,
            "context_retention": CONTEXT_RETENTION,
            "trained_after": trained_after,
            "related_before": related_before,
            "related_after": related_after,
            "related_gain": related_after - related_before,
            "reversed_after": reversed_after,
            "unrelated_training_delta": unrelated_after_training - unrelated_before,
            "unrelated_reversal_delta": unrelated_after_reversal - unrelated_after_training,
        }
        print(json.dumps(result, sort_keys=True))
        assert trained_after >= TRANSFER_MIN, result
        assert related_after >= TRANSFER_MIN, result
        assert reversed_after >= TRANSFER_MIN, result
        assert abs(unrelated_after_training - unrelated_before) <= UNRELATED_DRIFT_MAX, result
        assert abs(unrelated_after_reversal - unrelated_after_training) <= UNRELATED_DRIFT_MAX, result


if __name__ == "__main__":
    main()
