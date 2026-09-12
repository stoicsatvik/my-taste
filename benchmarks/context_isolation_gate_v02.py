from __future__ import annotations

import json
import tempfile
from pathlib import Path

from my_taste.core.context_isolation_engine import ContextIsolationTasteEngine

OLD_PREFERRED = "Short direct answer."
OLD_REJECTED = "We leverage innovative robust solutions to transform the dynamic ecosystem."
NEW_PREFERRED, NEW_REJECTED = OLD_REJECTED, OLD_PREFERRED
STABLE_PREFERRED = "Concise response."
STABLE_REJECTED = "Our cutting-edge seamless ecosystem unlocks innovative transformation."
CONTEXT_RETENTION = 0.75


def probability(engine, preferred, rejected, context):
    ranked = engine.rank_text([preferred, rejected], context=context)
    scores = {item.text: item.score for item in ranked}
    return engine._sigmoid(scores[preferred] - scores[rejected])


def main():
    with tempfile.TemporaryDirectory() as tmp:
        engine = ContextIsolationTasteEngine(Path(tmp) / "isolation.sqlite", context_retention=CONTEXT_RETENTION)
        for _ in range(8):
            engine.observe_choice(OLD_PREFERRED, OLD_REJECTED, context="chat")
        for _ in range(8):
            engine.observe_choice(STABLE_PREFERRED, STABLE_REJECTED, context="proposal")

        pre = probability(engine, NEW_PREFERRED, NEW_REJECTED, "chat")
        stable_before = probability(engine, STABLE_PREFERRED, STABLE_REJECTED, "proposal")
        trajectory = []
        adaptation_step = None
        for step in range(1, 9):
            engine.observe_choice(NEW_PREFERRED, NEW_REJECTED, context="chat")
            p = probability(engine, NEW_PREFERRED, NEW_REJECTED, "chat")
            trajectory.append(p)
            if adaptation_step is None and p >= 0.60:
                adaptation_step = step

        post = probability(engine, NEW_PREFERRED, NEW_REJECTED, "chat")
        stable_after = probability(engine, STABLE_PREFERRED, STABLE_REJECTED, "proposal")
        result = {
            "fixture": "synthetic-context-reversal-v1",
            "challenger": "context-isolation-recency-v1",
            "context_retention": CONTEXT_RETENTION,
            "pre": pre,
            "adaptation_step": adaptation_step,
            "post": post,
            "stable_before": stable_before,
            "stable_after": stable_after,
            "stable_delta": stable_after - stable_before,
            "trajectory": trajectory,
        }
        print(json.dumps(result, sort_keys=True))
        assert pre < 0.5, result
        assert adaptation_step is not None and adaptation_step <= 8, result
        assert post >= 0.65, result
        assert stable_after >= 0.65, result
        assert abs(stable_after - stable_before) <= 1e-12, result


if __name__ == "__main__":
    main()
