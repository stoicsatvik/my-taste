from __future__ import annotations

import json
import tempfile
from pathlib import Path

from my_taste.core.context_engine import ContextTasteEngine

# Frozen synthetic temporal gate. Do not tune this fixture after observing CI.
# Objective: determine whether the current cumulative V0.2 learner can adapt when a
# context-local preference reverses, without damaging an unrelated stable context.
OLD_PREFERRED = "Short direct answer."
OLD_REJECTED = "We leverage innovative robust solutions to transform the dynamic ecosystem."
NEW_PREFERRED = OLD_REJECTED
NEW_REJECTED = OLD_PREFERRED
STABLE_PREFERRED = "Concise response."
STABLE_REJECTED = "Our cutting-edge seamless ecosystem unlocks innovative transformation."

OLD_UPDATES = 8
REVERSAL_BUDGET = 8
STABLE_UPDATES = 8
ADAPT_THRESHOLD = 0.60
END_THRESHOLD = 0.65
RETENTION_THRESHOLD = 0.65


def probability(engine: ContextTasteEngine, preferred: str, rejected: str, context: str) -> float:
    ranked = engine.rank_text([preferred, rejected], context=context)
    scores = {item.text: item.score for item in ranked}
    return engine._sigmoid(scores[preferred] - scores[rejected])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = ContextTasteEngine(Path(tmp) / "drift.sqlite")

        for _ in range(OLD_UPDATES):
            engine.observe_choice(OLD_PREFERRED, OLD_REJECTED, context="chat")
        for _ in range(STABLE_UPDATES):
            engine.observe_choice(STABLE_PREFERRED, STABLE_REJECTED, context="proposal")

        pre_reversal_new = probability(engine, NEW_PREFERRED, NEW_REJECTED, "chat")
        stable_before = probability(engine, STABLE_PREFERRED, STABLE_REJECTED, "proposal")

        adaptation_step = None
        trajectory = []
        for step in range(1, REVERSAL_BUDGET + 1):
            engine.observe_choice(NEW_PREFERRED, NEW_REJECTED, context="chat")
            p = probability(engine, NEW_PREFERRED, NEW_REJECTED, "chat")
            trajectory.append(p)
            if adaptation_step is None and p >= ADAPT_THRESHOLD:
                adaptation_step = step

        post_reversal_new = probability(engine, NEW_PREFERRED, NEW_REJECTED, "chat")
        stable_after = probability(engine, STABLE_PREFERRED, STABLE_REJECTED, "proposal")
        retention_drop = stable_before - stable_after

        result = {
            "fixture": "synthetic-context-reversal-v1",
            "old_updates": OLD_UPDATES,
            "reversal_budget": REVERSAL_BUDGET,
            "stable_updates": STABLE_UPDATES,
            "adapt_threshold": ADAPT_THRESHOLD,
            "end_threshold": END_THRESHOLD,
            "retention_threshold": RETENTION_THRESHOLD,
            "pre_reversal_new_probability": pre_reversal_new,
            "adaptation_step": adaptation_step,
            "post_reversal_new_probability": post_reversal_new,
            "stable_probability_before": stable_before,
            "stable_probability_after": stable_after,
            "stable_retention_drop": retention_drop,
            "trajectory": trajectory,
        }
        print(json.dumps(result, sort_keys=True))

        # Preregistered promotion gate: reversal must be learned within an evidence
        # budget no larger than the history being overturned, and unrelated context
        # preference must remain discriminative. Failure is evidence, not a cue to
        # edit this fixture in place.
        assert pre_reversal_new < 0.5, result
        assert adaptation_step is not None and adaptation_step <= REVERSAL_BUDGET, result
        assert post_reversal_new >= END_THRESHOLD, result
        assert stable_after >= RETENTION_THRESHOLD, result


if __name__ == "__main__":
    main()
