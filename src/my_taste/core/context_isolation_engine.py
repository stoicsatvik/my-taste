from __future__ import annotations

from pathlib import Path

from my_taste.extractors.text import extract_text_features

from .context import normalize_context
from .context_engine import ContextTasteEngine
from .models import Evidence


class ContextIsolationTasteEngine(ContextTasteEngine):
    """Context challenger that prevents contextual evidence from mutating global weights.

    Context-free evidence still updates the domain-global profile. Context-scoped evidence
    updates only that context residual, preserving unrelated contexts under preference drift.
    """

    def __init__(self, db_path: str | Path, learning_rate: float = 1.0, context_retention: float = 0.75):
        super().__init__(db_path, learning_rate=learning_rate, context_retention=context_retention)

    def observe_choice(self, preferred: str, rejected: str, *, domain: str = "writing", context: str = "", source: str = "explicit_choice") -> dict[str, object]:
        if not preferred.strip() or not rejected.strip():
            raise ValueError("preferred and rejected text must both be non-empty")
        if preferred == rejected:
            raise ValueError("preferred and rejected text must differ")

        key = normalize_context(context)
        positive = extract_text_features(preferred)
        negative = extract_text_features(rejected)
        features = sorted(set(positive) | set(negative))
        delta = {feature: positive.get(feature, 0.0) - negative.get(feature, 0.0) for feature in features}
        current = self._effective_weights(domain, key)
        margin = sum(current.get(feature, 0.0) * value for feature, value in delta.items())
        probability = self._sigmoid(margin)
        step = self.learning_rate * (1.0 - probability)
        updates = {feature: step * value for feature, value in delta.items() if abs(value) > 1e-12}

        evidence = Evidence(
            kind="pairwise_text_choice",
            domain=domain,
            context=key,
            source=source,
            payload={
                "preferred": preferred,
                "rejected": rejected,
                "preferred_features": positive,
                "rejected_features": negative,
                "model_probability_before_update": probability,
                "context_key": key,
                "update_scope": "context" if key else "global",
            },
        )
        self.store.add_evidence(evidence)
        if key:
            self._update_context_weights(domain, key, updates)
        else:
            self.store.update_weights(domain, updates)

        strongest = sorted(updates.items(), key=lambda item: abs(item[1]), reverse=True)[:5]
        return {
            "evidence_id": evidence.id,
            "domain": domain,
            "context": key,
            "probability_before_update": probability,
            "updated_features": dict(strongest),
            "update_scope": "context" if key else "global",
        }
