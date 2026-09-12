from __future__ import annotations

import json
import tempfile
from pathlib import Path

from my_taste.core.context_isolation_engine import ContextIsolationTasteEngine

PREFERRED = "Short direct answer."
REJECTED = "We leverage innovative robust solutions to transform the dynamic ecosystem."
REVERSED_PREFERRED, REVERSED_REJECTED = REJECTED, PREFERRED
TRAIN_CONTEXT = "work-email"
RELATED_UNSEEN_CONTEXT = "work-memo"
UNRELATED_CONTEXT = "casual-chat"
TRAIN_OBSERVATIONS = 8
REVERSAL_OBSERVATIONS = 8
RELATED_TRANSFER_MIN = 0.60
UNRELATED_DRIFT_MAX = 1e-12
CONTEXT_RETENTION = 0.75


def probability(engine, preferred: str, rejected: str, context: str) -> float:
    ranked = engine.rank_text([preferred, rejected], context=context)
    scores = {item.text: item.score for item in ranked}
    return engine._sigmoid(scores[preferred] - scores[rejected])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = ContextIsolationTasteEngine(
            Path(tmp) / "transfer.sqlite",
            context_retention=CONTEXT_RETENTION,
        )

        related_before = probability(engine, PREFERRED, REJECTED, RELATED_UNSEEN_CONTEXT)
        unrelated_before = probability(engine, PREFERRED, REJECTED, UNRELATED_CONTEXT)

        for _ in range(TRAIN_OBSERVATIONS):
            engine.observe_choice(PREFERRED, REJECTED, context=TRAIN_CONTEXT)

        train_after = probability(engine, PREFERRED, REJECTED, TRAIN_CONTEXT)
        related_after = probability(engine, PREFERRED, REJECTED, RELATED_UNSEEN_CONTEXT)
        unrelated_after_training = probability(engine, PREFERRED, REJECTED, UNRELATED_CONTEXT)

        for _ in range(REVERSAL_OBSERVATIONS):
            engine.observe_choice(REVERSED_PREFERRED, REVERSED_REJECTED, context=TRAIN_CONTEXT)

        unrelated_after_reversal = probability(engine, PREFERRED, REJECTED, UNRELATED_CONTEXT)

        result = {
            "fixture": "synthetic-related-context-transfer-v1",
            "challenger": "context-isolation-recency-v1",
            "context_retention": CONTEXT_RETENTION,
            "train_observations": TRAIN_OBSERVATIONS,
            "reversal_observations": REVERSAL_OBSERVATIONS,
            "related_transfer_min": RELATED_TRANSFER_MIN,
            "unrelated_drift_max": UNRELATED_DRIFT_MAX,
            "related_before": related_before,
            "train_after": train_after,
            "related_after": related_after,
            "related_gain": related_after - related_before,
            "unrelated_before": unrelated_before,
            "unrelated_after_training": unrelated_after_training,
            "unrelated_after_reversal": unrelated_after_reversal,
            "unrelated_training_delta": unrelated_after_training - unrelated_before,
            "unrelated_reversal_delta": unrelated_after_reversal - unrelated_after_training,
        }
        print(json.dumps(result, sort_keys=True))

        # Frozen transfer-vs-interference gate: contextual evidence should help a
        # semantically related unseen context while leaving an unrelated context
        # unchanged, including after a local reversal. This fixture is synthetic
        # and tests architecture semantics only, not real-user generalization.
        assert train_after >= RELATED_TRANSFER_MIN, result
        assert related_after >= RELATED_TRANSFER_MIN, result
        assert abs(unrelated_after_training - unrelated_before) <= UNRELATED_DRIFT_MAX, result
        assert abs(unrelated_after_reversal - unrelated_after_training) <= UNRELATED_DRIFT_MAX, result


if __name__ == "__main__":
    main()
