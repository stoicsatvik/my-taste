from __future__ import annotations

from .context import normalize_context
from .context_isolation_engine import ContextIsolationTasteEngine


class HierarchicalContextTasteEngine(ContextIsolationTasteEngine):
    """Explicit context-family sharing without contextual updates to global weights."""

    def __init__(self, db_path, *, context_families: dict[str, str], learning_rate: float = 1.0, context_retention: float = 0.75, family_share: float = 0.35):
        super().__init__(db_path, learning_rate=learning_rate, context_retention=context_retention)
        if not 0.0 < family_share < 1.0:
            raise ValueError("family_share must be in (0, 1)")
        self.family_share = float(family_share)
        self.context_families = {normalize_context(k): normalize_context(v) for k, v in context_families.items()}

    def _family_key(self, context: str) -> str:
        family = self.context_families.get(normalize_context(context), "")
        return f"family-{family}" if family else ""

    def _effective_weights(self, domain: str, context: str = "") -> dict[str, float]:
        effective = {feature: item.weight for feature, item in self.store.get_weights(domain).items()}
        family_key = self._family_key(context)
        if family_key:
            for feature, item in self.get_context_weights(domain, family_key).items():
                effective[feature] = effective.get(feature, 0.0) + item.weight
        for feature, item in self.get_context_weights(domain, context).items():
            effective[feature] = effective.get(feature, 0.0) + item.weight
        return effective

    def _update_context_weights(self, domain: str, context: str, deltas: dict[str, float]) -> None:
        key = normalize_context(context)
        family_key = self._family_key(key)
        if family_key and not key.startswith("family-"):
            super()._update_context_weights(domain, family_key, {f: d * self.family_share for f, d in deltas.items()})
            super()._update_context_weights(domain, key, {f: d * (1.0 - self.family_share) for f, d in deltas.items()})
            return
        super()._update_context_weights(domain, key, deltas)
