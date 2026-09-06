from __future__ import annotations

import math
from pathlib import Path

from my_taste.extractors.text import extract_text_features

from .models import Evidence, RankedCandidate
from .store import SQLiteTasteStore


class TasteEngine:
    def __init__(self, db_path: str | Path, learning_rate: float = 1.0, context_strength: float = 1.0):
        if learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if context_strength < 0:
            raise ValueError("context_strength must be non-negative")
        self.store = SQLiteTasteStore(db_path)
        self.learning_rate = float(learning_rate)
        self.context_strength = float(context_strength)

    @staticmethod
    def _sigmoid(value: float) -> float:
        if value >= 0:
            z = math.exp(-value)
            return 1.0 / (1.0 + z)
        z = math.exp(value)
        return z / (1.0 + z)

    @staticmethod
    def _context_key(domain: str, context: str) -> str:
        normalized = " ".join(context.strip().lower().split())
        return f"{domain}::context::{normalized}" if normalized else ""

    def _combined_weights(self, domain: str, context: str = "") -> dict[str, float]:
        combined = {name: item.weight for name, item in self.store.get_weights(domain).items()}
        context_key = self._context_key(domain, context)
        if context_key:
            for name, item in self.store.get_weights(context_key).items():
                combined[name] = combined.get(name, 0.0) + self.context_strength * item.weight
        return combined

    def _score_features(self, features: dict[str, float], domain: str, context: str = "") -> tuple[float, dict[str, float]]:
        weights = self._combined_weights(domain, context)
        contributions = {feature: weights[feature] * value for feature, value in features.items() if feature in weights}
        return sum(contributions.values()), contributions

    def observe_choice(
        self,
        preferred: str,
        rejected: str,
        *,
        domain: str = "writing",
        context: str = "",
        source: str = "explicit_choice",
    ) -> dict[str, object]:
        if not preferred.strip() or not rejected.strip():
            raise ValueError("preferred and rejected text must both be non-empty")
        if preferred == rejected:
            raise ValueError("preferred and rejected text must differ")

        positive = extract_text_features(preferred)
        negative = extract_text_features(rejected)
        features = sorted(set(positive) | set(negative))
        delta = {f: positive.get(f, 0.0) - negative.get(f, 0.0) for f in features}

        current = self._combined_weights(domain, context)
        margin = sum(current.get(f, 0.0) * d for f, d in delta.items())
        probability = self._sigmoid(margin)
        step = self.learning_rate * (1.0 - probability)
        updates = {f: step * d for f, d in delta.items() if abs(d) > 1e-12}

        evidence = Evidence(
            kind="pairwise_text_choice",
            domain=domain,
            context=context,
            source=source,
            payload={
                "preferred": preferred,
                "rejected": rejected,
                "preferred_features": positive,
                "rejected_features": negative,
                "model_probability_before_update": probability,
            },
        )
        self.store.add_evidence(evidence)
        self.store.update_weights(domain, updates)
        context_key = self._context_key(domain, context)
        if context_key:
            self.store.update_weights(context_key, updates)

        strongest = sorted(updates.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        return {
            "evidence_id": evidence.id,
            "domain": domain,
            "context": context,
            "probability_before_update": probability,
            "updated_features": dict(strongest),
        }

    def observe_edit(self, original: str, edited: str, *, domain: str = "writing", context: str = "") -> dict[str, object]:
        return self.observe_choice(edited, original, domain=domain, context=context, source="user_edit")

    def rank_text(self, candidates: list[str], *, domain: str = "writing", context: str = "") -> list[RankedCandidate]:
        if not candidates:
            return []
        ranked: list[RankedCandidate] = []
        for text in candidates:
            features = extract_text_features(text)
            score, contributions = self._score_features(features, domain, context)
            ranked.append(RankedCandidate(text=text, score=score, features=features, contributions=contributions))
        ranked.sort(key=lambda c: c.score, reverse=True)
        return ranked

    def pairwise_probability(self, candidate_a: str, candidate_b: str, *, domain: str = "writing", context: str = "") -> float:
        a_score, _ = self._score_features(extract_text_features(candidate_a), domain, context)
        b_score, _ = self._score_features(extract_text_features(candidate_b), domain, context)
        return self._sigmoid(a_score - b_score)

    def profile(self, *, domain: str = "writing", limit: int = 20) -> list[dict[str, object]]:
        weights = self.store.get_weights(domain)
        ordered = sorted(weights.values(), key=lambda w: abs(w.weight), reverse=True)
        return [{"feature": w.feature, "direction": "prefer_more" if w.weight > 0 else "prefer_less", "weight": w.weight, "confidence": w.confidence, "updates": w.updates, "updated_at": w.updated_at} for w in ordered[: max(1, min(limit, 200))]]

    def explain_text(self, text: str, *, domain: str = "writing", context: str = "", limit: int = 5) -> dict[str, object]:
        features = extract_text_features(text)
        score, contributions = self._score_features(features, domain, context)
        strongest = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)[:limit]
        return {"score": score, "features": features, "strongest_contributions": [{"feature": feature, "contribution": contribution, "effect": "helps" if contribution > 0 else "hurts"} for feature, contribution in strongest]}
