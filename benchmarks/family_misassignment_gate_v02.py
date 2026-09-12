from __future__ import annotations

import json
import tempfile
from pathlib import Path

from my_taste.core.hierarchical_context_engine import HierarchicalContextTasteEngine

PREFERRED = "Short direct answer."
REJECTED = "We leverage innovative robust solutions to transform the dynamic ecosystem."
TRAIN_CONTEXT = "work-email"
RELATED_CONTEXT = "work-memo"
MISASSIGNED_CONTEXT = "casual-chat"
# Deliberately wrong metadata: casual-chat is assigned to the work family.
FAMILIES = {
    TRAIN_CONTEXT: "work",
    RELATED_CONTEXT: "work",
    MISASSIGNED_CONTEXT: "work",
}
OBSERVATIONS = 8
TRANSFER_MIN = 0.60
MISASSIGNMENT_DRIFT_MAX = 0.05
FAMILY_SHARE = 0.35
CONTEXT_RETENTION = 0.75


def probability(engine, preferred: str, rejected: str, context: str) -> float:
    ranked = engine.rank_text([preferred, rejected], context=context)
    scores = {item.text: item.score for item in ranked}
    return engine._sigmoid(scores[preferred] - scores[rejected])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = HierarchicalContextTasteEngine(
            Path(tmp) / "misassignment.sqlite",
            context_families=FAMILIES,
            family_share=FAMILY_SHARE,
            context_retention=CONTEXT_RETENTION,
        )
        related_before = probability(engine, PREFERRED, REJECTED, RELATED_CONTEXT)
        misassigned_before = probability(engine, PREFERRED, REJECTED, MISASSIGNED_CONTEXT)
        for _ in range(OBSERVATIONS):
            engine.observe_choice(PREFERRED, REJECTED, context=TRAIN_CONTEXT)
        related_after = probability(engine, PREFERRED, REJECTED, RELATED_CONTEXT)
        misassigned_after = probability(engine, PREFERRED, REJECTED, MISASSIGNED_CONTEXT)
        result = {
            "fixture": "synthetic-family-misassignment-v1",
            "challenger": "explicit-family-hierarchy-v1",
            "family_share": FAMILY_SHARE,
            "context_retention": CONTEXT_RETENTION,
            "related_before": related_before,
            "related_after": related_after,
            "related_gain": related_after - related_before,
            "misassigned_before": misassigned_before,
            "misassigned_after": misassigned_after,
            "misassignment_drift": misassigned_after - misassigned_before,
        }
        print(json.dumps(result, sort_keys=True))
        assert related_after >= TRANSFER_MIN, result
        assert abs(misassigned_after - misassigned_before) <= MISASSIGNMENT_DRIFT_MAX, result


if __name__ == "__main__":
    main()
