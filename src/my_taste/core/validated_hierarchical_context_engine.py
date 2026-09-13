from __future__ import annotations

from .context import normalize_context
from .hierarchical_context_engine import HierarchicalContextTasteEngine


class ValidatedHierarchicalContextTasteEngine(HierarchicalContextTasteEngine):
    """Hierarchy whose family transfer is gated by independently supplied membership confidence.

    Confidence is deliberately separate from caller family labels. A family label alone has
    zero authority: missing confidence means no family sharing. This challenger does not infer
    semantic relatedness; it only makes the trust boundary explicit and testable.
    """

    def __init__(
        self,
        db_path,
        *,
        context_families: dict[str, str],
        family_confidence: dict[str, float],
        learning_rate: float = 1.0,
        context_retention: float = 0.75,
        family_share: float = 0.35,
    ):
        super().__init__(
            db_path,
            context_families=context_families,
            learning_rate=learning_rate,
            context_retention=context_retention,
            family_share=family_share,
        )
        self.family_confidence = {}
        for context, confidence in family_confidence.items():
            value = float(confidence)
            if not 0.0 <= value <= 1.0:
                raise ValueError("family confidence must be in [0, 1]")
            self.family_confidence[normalize_context(context)] = value

    def _membership_confidence(self, context: str) -> float:
        return self.family_confidence.get(normalize_context(context), 0.0)

    def _effective_weights(self, domain: str, context: str = "") -> dict[str, float]:
        effective = {feature: item.weight for feature, item in self.store.get_weights(domain).items()}
        key = normalize_context(context)
        family_key = self._family_key(key)
        confidence = self._membership_confidence(key)
        if family_key and confidence > 0.0:
            for feature, item in self.get_context_weights(domain, family_key).items():
                effective[feature] = effective.get(feature, 0.0) + item.weight * confidence
        for feature, item in self.get_context_weights(domain, key).items():
            effective[feature] = effective.get(feature, 0.0) + item.weight
        return effective

    def _update_context_weights(self, domain: str, context: str, deltas: dict[str, float]) -> None:
        key = normalize_context(context)
        family_key = self._family_key(key)
        confidence = self._membership_confidence(key)
        if family_key and not key.startswith("family-") and confidence > 0.0:
            shared = self.family_share * confidence
            super(HierarchicalContextTasteEngine, self)._update_context_weights(
                domain, family_key, {feature: delta * shared for feature, delta in deltas.items()}
            )
            super(HierarchicalContextTasteEngine, self)._update_context_weights(
                domain, key, {feature: delta * (1.0 - shared) for feature, delta in deltas.items()}
            )
            return
        super(HierarchicalContextTasteEngine, self)._update_context_weights(domain, key, deltas)
