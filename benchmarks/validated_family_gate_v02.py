from __future__ import annotations

import json
import tempfile
from pathlib import Path

from my_taste.core.validated_hierarchical_context_engine import ValidatedHierarchicalContextTasteEngine

PREFERRED = "Short direct answer."
REJECTED = "We leverage innovative robust solutions to transform the dynamic ecosystem."
TRAIN_CONTEXT = "work-email"
RELATED_CONTEXT = "work-memo"
MISASSIGNED_CONTEXT = "casual-chat"
FAMILIES = {TRAIN_CONTEXT: "work", RELATED_CONTEXT: "work", MISASSIGNED_CONTEXT: "work"}
# Confidence is an independently supplied validation signal, not derived from this holdout.
CONFIDENCE = {TRAIN_CONTEXT: 1.0, RELATED_CONTEXT: 1.0, MISASSIGNED_CONTEXT: 0.0}
OBSERVATIONS = 8
TRANSFER_MIN = 0.60
MISASSIGNMENT_DRIFT_MAX = 0.05
FAMILY_SHARE = 0.35
CONTEXT_RETENTION = 0.75


def probability(engine, context: str) -> float:
    ranked = engine.rank_text([PREFERRED, REJECTED], context=context)
    scores = {item.text: item.score for item in ranked}
    return engine._sigmoid(scores[PREFERRED] - scores[REJECTED])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = ValidatedHierarchicalContextTasteEngine(
            Path(tmp) / "validated-family.sqlite",
            context_families=FAMILIES,
            family_confidence=CONFIDENCE,
            family_share=FAMILY_SHARE,
            context_retention=CONTEXT_RETENTION,
        )
        related_before = probability(engine, RELATED_CONTEXT)
        misassigned_before = probability(engine, MISASSIGNED_CONTEXT)
        for _ in range(OBSERVATIONS):
            engine.observe_choice(PREFERRED, REJECTED, context=TRAIN_CONTEXT)
        related_after = probability(engine, RELATED_CONTEXT)
        misassigned_after = probability(engine, MISASSIGNED_CONTEXT)
        result = {
            "fixture": "synthetic-validated-family-v1",
            "challenger": "confidence-gated-family-v1",
            "family_share": FAMILY_SHARE,
            "related_before": related_before,
            "related_after": related_after,
            "misassigned_before": misassigned_before,
            "misassigned_after": misassigned_after,
            "misassignment_drift": misassigned_after - misassigned_before,
        }
        print(json.dumps(result, sort_keys=True))
        assert related_after >= TRANSFER_MIN, result
        assert abs(misassigned_after - misassigned_before) <= MISASSIGNMENT_DRIFT_MAX, result


if __name__ == "__main__":
    main()
