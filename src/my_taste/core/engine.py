from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from my_taste.extractors.text import extract_text_features

from .models import Evidence, RankedCandidate, TasteEvidence
from .store import SQLiteTasteStore

_TOKEN_RE = re.compile(r"[A-Za-z0-9_+#.-]+")


class TasteEngine:
    def __init__(self, db_path: str | Path, learning_rate: float = 1.0):
        if learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        self.store = SQLiteTasteStore(db_path)
        self.learning_rate = float(learning_rate)

    @staticmethod
    def _sigmoid(value: float) -> float:
        if value >= 0:
            z = math.exp(-value)
            return 1.0 / (1.0 + z)
        z = math.exp(value)
        return z / (1.0 + z)

    @staticmethod
    def _tokens(value: object) -> set[str]:
        return {token.lower() for token in _TOKEN_RE.findall(str(value)) if token}

    @classmethod
    def _jaccard(cls, left: object, right: object) -> float:
        a = cls._tokens(left)
        b = cls._tokens(right)
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    @classmethod
    def _context_similarity(
        cls,
        query: dict[str, str],
        stored: dict[str, str],
    ) -> float:
        if not query:
            return 0.5
        if not stored:
            return 0.0

        pair_scores: list[float] = []
        for key, value in query.items():
            if key in stored:
                pair_scores.append(1.0 if stored[key] == value else cls._jaccard(value, stored[key]))
            else:
                pair_scores.append(0.0)

        exactish = sum(pair_scores) / max(1, len(pair_scores))
        query_text = " ".join(f"{k} {v}" for k, v in query.items())
        stored_text = " ".join(f"{k} {v}" for k, v in stored.items())
        lexical = cls._jaccard(query_text, stored_text)
        return 0.75 * exactish + 0.25 * lexical

    @staticmethod
    def _recency(created_at: str) -> float:
        try:
            stamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age_days = max(0.0, (datetime.now(timezone.utc) - stamp).total_seconds() / 86400.0)
        except (TypeError, ValueError):
            return 0.0
        return 1.0 / (1.0 + age_days / 180.0)

    @classmethod
    def _feature_similarity(cls, left: object, right: object) -> float:
        if isinstance(left, bool) and isinstance(right, bool):
            return 1.0 if left == right else 0.0

        numeric = (int, float)
        if (
            isinstance(left, numeric)
            and not isinstance(left, bool)
            and isinstance(right, numeric)
            and not isinstance(right, bool)
        ):
            scale = max(1.0, abs(float(left)), abs(float(right)))
            return max(0.0, 1.0 - abs(float(left) - float(right)) / scale)

        if isinstance(left, list) and isinstance(right, list):
            a = {str(v).lower() for v in left}
            b = {str(v).lower() for v in right}
            if not a and not b:
                return 1.0
            if not a or not b:
                return 0.0
            return len(a & b) / len(a | b)

        return cls._jaccard(left, right)

    def _score_features(self, features: dict[str, float], domain: str) -> tuple[float, dict[str, float]]:
        weights = self.store.get_weights(domain)
        contributions = {
            feature: weights[feature].weight * value
            for feature, value in features.items()
            if feature in weights
        }
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

        current = self.store.get_weights(domain)
        margin = sum(current[f].weight * d for f, d in delta.items() if f in current)
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

        strongest = sorted(updates.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        return {
            "evidence_id": evidence.id,
            "domain": domain,
            "probability_before_update": probability,
            "updated_features": dict(strongest),
        }

    def observe_edit(
        self,
        original: str,
        edited: str,
        *,
        domain: str = "writing",
        context: str = "",
    ) -> dict[str, object]:
        return self.observe_choice(
            edited,
            original,
            domain=domain,
            context=context,
            source="user_edit",
        )

    def observe_artifact(
        self,
        *,
        domain: str,
        modality: str,
        features: dict[str, Any],
        context: dict[str, str] | None = None,
        preference: str = "positive",
        strength: float = 1.0,
        source: str = "explicit_like",
        source_reference: str = "",
        note: str = "",
    ) -> dict[str, object]:
        domain = domain.strip().lower()
        modality = modality.strip().lower()
        preference = preference.strip().lower()

        if not domain:
            raise ValueError("domain must be non-empty")
        if not modality:
            raise ValueError("modality must be non-empty")
        if preference not in {"positive", "negative"}:
            raise ValueError("preference must be 'positive' or 'negative'")
        if not features:
            raise ValueError("features must be non-empty")
        if strength <= 0:
            raise ValueError("strength must be positive")

        clean_context = {
            str(key).strip(): str(value).strip()
            for key, value in (context or {}).items()
            if str(key).strip() and str(value).strip()
        }
        clean_features = {
            str(key).strip(): value
            for key, value in features.items()
            if str(key).strip() and value is not None
        }
        if not clean_features:
            raise ValueError("features must contain at least one usable feature")

        evidence = TasteEvidence(
            domain=domain,
            modality=modality,
            features=clean_features,
            context=clean_context,
            preference=preference,
            strength=float(strength),
            source=source,
            source_reference=source_reference,
            note=note,
        )
        self.store.add_taste_evidence(evidence)
        return {
            "evidence_id": evidence.id,
            "domain": evidence.domain,
            "modality": evidence.modality,
            "preference": evidence.preference,
            "feature_count": len(evidence.features),
            "context": evidence.context,
        }

    def retrieve_taste(
        self,
        *,
        domain: str,
        context: dict[str, str] | None = None,
        modality: str = "",
        limit: int = 8,
    ) -> list[dict[str, object]]:
        domain = domain.strip().lower()
        modality = modality.strip().lower()
        if not domain:
            raise ValueError("domain must be non-empty")

        query_context = {
            str(key).strip(): str(value).strip()
            for key, value in (context or {}).items()
            if str(key).strip() and str(value).strip()
        }

        results: list[dict[str, object]] = []
        for evidence in self.store.taste_evidence(domain, limit=500):
            context_score = self._context_similarity(query_context, evidence.context)
            modality_score = 0.0
            if modality:
                modality_score = 0.18 if modality == evidence.modality else -0.05

            relevance = (
                0.20
                + 0.55 * context_score
                + modality_score
                + 0.07 * self._recency(evidence.created_at)
            )
            relevance *= min(2.0, max(0.1, evidence.strength))

            results.append(
                {
                    "id": evidence.id,
                    "domain": evidence.domain,
                    "modality": evidence.modality,
                    "preference": evidence.preference,
                    "strength": evidence.strength,
                    "context": evidence.context,
                    "features": evidence.features,
                    "source": evidence.source,
                    "source_reference": evidence.source_reference,
                    "note": evidence.note,
                    "created_at": evidence.created_at,
                    "relevance": round(max(0.0, relevance), 6),
                }
            )

        results.sort(key=lambda item: float(item["relevance"]), reverse=True)
        return results[: max(1, min(int(limit), 100))]


    def taste_brief(
        self,
        *,
        domain: str,
        context: dict[str, str] | None = None,
        modality: str = "",
        limit: int = 12,
        min_relevance: float = 0.35,
    ) -> dict[str, object]:
        """Summarize context-relevant evidence into actionable prefer/avoid guidance."""
        evidence = [
            item
            for item in self.retrieve_taste(
                domain=domain,
                context=context,
                modality=modality,
                limit=max(limit * 4, 24),
            )
            if float(item["relevance"]) >= min_relevance
        ][: max(1, min(int(limit), 100))]

        buckets: dict[tuple[str, str], dict[str, object]] = {}
        for item in evidence:
            features = item.get("features", {})
            if not isinstance(features, dict):
                continue
            sign = str(item.get("preference", "positive"))
            weight = float(item.get("relevance", 0.0))
            for feature, value in features.items():
                key = (str(feature), repr(value))
                bucket = buckets.setdefault(
                    key,
                    {
                        "feature": str(feature),
                        "value": value,
                        "positive": 0.0,
                        "negative": 0.0,
                        "evidence_ids": [],
                    },
                )
                if sign == "positive":
                    bucket["positive"] = float(bucket["positive"]) + weight
                else:
                    bucket["negative"] = float(bucket["negative"]) + weight
                cast_ids = bucket["evidence_ids"]
                if isinstance(cast_ids, list):
                    cast_ids.append(str(item["id"]))

        prefer: list[dict[str, object]] = []
        avoid: list[dict[str, object]] = []
        conflicts: list[dict[str, object]] = []

        for bucket in buckets.values():
            positive = float(bucket["positive"])
            negative = float(bucket["negative"])
            support = positive + negative
            if support <= 0:
                continue

            net = positive - negative
            dominance = abs(net) / support
            evidence_confidence = 1.0 - math.exp(-support / 1.5)
            confidence = round(dominance * evidence_confidence, 6)

            row = {
                "feature": bucket["feature"],
                "value": bucket["value"],
                "support": round(support, 6),
                "confidence": confidence,
                "evidence_ids": bucket["evidence_ids"][:5],
            }

            if positive > 0 and negative > 0:
                conflicts.append(
                    {
                        **row,
                        "positive_support": round(positive, 6),
                        "negative_support": round(negative, 6),
                    }
                )

            if net > 0:
                prefer.append(row)
            elif net < 0:
                avoid.append(row)

        prefer.sort(key=lambda row: (float(row["confidence"]), float(row["support"])), reverse=True)
        avoid.sort(key=lambda row: (float(row["confidence"]), float(row["support"])), reverse=True)
        conflicts.sort(key=lambda row: float(row["support"]), reverse=True)

        overall_support = sum(float(item["relevance"]) for item in evidence)
        overall_confidence = 0.0 if not evidence else 1.0 - math.exp(-overall_support / 4.0)

        return {
            "domain": domain.strip().lower(),
            "modality": modality.strip().lower(),
            "context": context or {},
            "evidence_count": len(evidence),
            "confidence": round(overall_confidence, 6),
            "prefer": prefer[:10],
            "avoid": avoid[:10],
            "conflicts": conflicts[:10],
        }

    def rank_profiles(
        self,
        candidates: list[dict[str, Any]],
        *,
        domain: str,
        context: dict[str, str] | None = None,
        modality: str = "",
    ) -> list[dict[str, object]]:
        evidence = self.retrieve_taste(
            domain=domain,
            context=context,
            modality=modality,
            limit=50,
        )

        ranked: list[dict[str, object]] = []
        for index, candidate in enumerate(candidates):
            features = candidate.get("features", {})
            if not isinstance(features, dict) or not features:
                raise ValueError("each candidate must contain a non-empty 'features' object")

            total = 0.0
            denominator = 0.0
            strongest: list[dict[str, object]] = []

            for item in evidence:
                stored = item["features"]
                if not isinstance(stored, dict):
                    continue
                common = sorted(set(features) & set(stored))
                if not common:
                    continue

                per_feature = [
                    self._feature_similarity(features[name], stored[name])
                    for name in common
                ]
                similarity = sum(per_feature) / len(per_feature)
                sign = 1.0 if item["preference"] == "positive" else -1.0
                weight = float(item["relevance"])
                contribution = sign * similarity * weight
                total += contribution
                denominator += abs(weight)
                strongest.append(
                    {
                        "evidence_id": item["id"],
                        "similarity": round(similarity, 6),
                        "effect": "helps" if contribution >= 0 else "hurts",
                        "contribution": round(contribution, 6),
                    }
                )

            score = total / denominator if denominator else 0.0
            strongest.sort(key=lambda row: abs(float(row["contribution"])), reverse=True)
            ranked.append(
                {
                    "id": candidate.get("id", str(index)),
                    "label": candidate.get("label", ""),
                    "score": round(score, 6),
                    "evidence_matches": strongest[:5],
                }
            )

        ranked.sort(key=lambda row: float(row["score"]), reverse=True)
        return ranked

    def rank_text(self, candidates: list[str], *, domain: str = "writing") -> list[RankedCandidate]:
        if not candidates:
            return []
        ranked: list[RankedCandidate] = []
        for text in candidates:
            features = extract_text_features(text)
            score, contributions = self._score_features(features, domain)
            ranked.append(
                RankedCandidate(
                    text=text,
                    score=score,
                    features=features,
                    contributions=contributions,
                )
            )
        ranked.sort(key=lambda c: c.score, reverse=True)
        return ranked

    def profile(self, *, domain: str = "writing", limit: int = 20) -> list[dict[str, object]]:
        weights = self.store.get_weights(domain)
        ordered = sorted(weights.values(), key=lambda w: abs(w.weight), reverse=True)
        return [
            {
                "feature": w.feature,
                "direction": "prefer_more" if w.weight > 0 else "prefer_less",
                "weight": w.weight,
                "confidence": w.confidence,
                "updates": w.updates,
                "updated_at": w.updated_at,
            }
            for w in ordered[: max(1, min(limit, 200))]
        ]

    def explain_text(self, text: str, *, domain: str = "writing", limit: int = 5) -> dict[str, object]:
        features = extract_text_features(text)
        score, contributions = self._score_features(features, domain)
        strongest = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)[:limit]
        return {
            "score": score,
            "features": features,
            "strongest_contributions": [
                {
                    "feature": feature,
                    "contribution": contribution,
                    "effect": "helps" if contribution > 0 else "hurts",
                }
                for feature, contribution in strongest
            ],
        }
