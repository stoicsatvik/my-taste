from __future__ import annotations

import math
import sqlite3
from pathlib import Path

from my_taste.extractors.text import extract_text_features

from .context import normalize_context, preference_instruction
from .engine import TasteEngine
from .models import Evidence, PreferenceWeight, RankedCandidate, utc_now_iso


class ContextTasteEngine(TasteEngine):
    """V0.2 challenger: global preference learning plus exact context residuals."""

    def __init__(self, db_path: str | Path, learning_rate: float = 1.0, context_retention: float = 1.0):
        super().__init__(db_path, learning_rate=learning_rate)
        if not 0.0 < context_retention <= 1.0:
            raise ValueError("context_retention must be in (0, 1]")
        self.context_retention = float(context_retention)
        self._init_context_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.store.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_context_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS context_preference_weights (
                    domain TEXT NOT NULL, context TEXT NOT NULL, feature TEXT NOT NULL,
                    weight REAL NOT NULL, updates INTEGER NOT NULL, updated_at TEXT NOT NULL,
                    PRIMARY KEY(domain, context, feature)
                );
                CREATE INDEX IF NOT EXISTS idx_context_weights_domain_context
                ON context_preference_weights(domain, context);
            """)

    def get_context_weights(self, domain: str, context: str) -> dict[str, PreferenceWeight]:
        key = normalize_context(context)
        if not key:
            return {}
        with self._connect() as conn:
            rows = conn.execute("SELECT domain, feature, weight, updates, updated_at FROM context_preference_weights WHERE domain = ? AND context = ?", (domain, key)).fetchall()
        return {row["feature"]: PreferenceWeight(domain=row["domain"], feature=row["feature"], weight=float(row["weight"]), updates=int(row["updates"]), updated_at=row["updated_at"]) for row in rows}

    def _update_context_weights(self, domain: str, context: str, deltas: dict[str, float]) -> None:
        key = normalize_context(context)
        if not key:
            return
        now = utc_now_iso()
        with self._connect() as conn:
            for feature, delta in deltas.items():
                conn.execute("""
                    INSERT INTO context_preference_weights (domain, context, feature, weight, updates, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                    ON CONFLICT(domain, context, feature) DO UPDATE SET
                        weight = context_preference_weights.weight * ? + excluded.weight,
                        updates = context_preference_weights.updates + 1,
                        updated_at = excluded.updated_at
                """, (domain, key, feature, float(delta), now, self.context_retention))

    def _effective_weights(self, domain: str, context: str = "") -> dict[str, float]:
        global_weights = self.store.get_weights(domain)
        effective = {feature: item.weight for feature, item in global_weights.items()}
        for feature, item in self.get_context_weights(domain, context).items():
            effective[feature] = effective.get(feature, 0.0) + item.weight
        return effective

    def _score_contextual_features(self, features: dict[str, float], domain: str, context: str = "") -> tuple[float, dict[str, float]]:
        weights = self._effective_weights(domain, context)
        contributions = {feature: weights[feature] * value for feature, value in features.items() if feature in weights}
        return sum(contributions.values()), contributions

    def observe_choice(self, preferred: str, rejected: str, *, domain: str = "writing", context: str = "", source: str = "explicit_choice") -> dict[str, object]:
        if not preferred.strip() or not rejected.strip():
            raise ValueError("preferred and rejected text must both be non-empty")
        if preferred == rejected:
            raise ValueError("preferred and rejected text must differ")
        key = normalize_context(context)
        positive = extract_text_features(preferred)
        negative = extract_text_features(rejected)
        features = sorted(set(positive) | set(negative))
        delta = {f: positive.get(f, 0.0) - negative.get(f, 0.0) for f in features}
        current = self._effective_weights(domain, key)
        margin = sum(current.get(f, 0.0) * d for f, d in delta.items())
        probability = self._sigmoid(margin)
        step = self.learning_rate * (1.0 - probability)
        updates = {f: step * d for f, d in delta.items() if abs(d) > 1e-12}
        evidence = Evidence(kind="pairwise_text_choice", domain=domain, context=key, source=source, payload={"preferred": preferred, "rejected": rejected, "preferred_features": positive, "rejected_features": negative, "model_probability_before_update": probability, "context_key": key})
        self.store.add_evidence(evidence)
        self.store.update_weights(domain, updates)
        if key:
            self._update_context_weights(domain, key, updates)
        strongest = sorted(updates.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        return {"evidence_id": evidence.id, "domain": domain, "context": key, "probability_before_update": probability, "updated_features": dict(strongest)}

    def rank_text(self, candidates: list[str], *, domain: str = "writing", context: str = "") -> list[RankedCandidate]:
        ranked = []
        for text in candidates:
            features = extract_text_features(text)
            score, contributions = self._score_contextual_features(features, domain, context)
            ranked.append(RankedCandidate(text=text, score=score, features=features, contributions=contributions))
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked

    def context_profile(self, *, domain: str = "writing", context: str = "", limit: int = 20) -> list[dict[str, object]]:
        key = normalize_context(context)
        global_weights = self.store.get_weights(domain)
        local_weights = self.get_context_weights(domain, key)
        rows = []
        for feature in set(global_weights) | set(local_weights):
            global_weight = global_weights.get(feature)
            local_weight = local_weights.get(feature)
            effective = (global_weight.weight if global_weight else 0.0) + (local_weight.weight if local_weight else 0.0)
            updates = max(global_weight.updates if global_weight else 0, local_weight.updates if local_weight else 0)
            rows.append({"feature": feature, "direction": "prefer_more" if effective > 0 else "prefer_less", "effective_weight": effective, "global_weight": global_weight.weight if global_weight else 0.0, "context_weight": local_weight.weight if local_weight else 0.0, "confidence": 1.0 - math.exp(-updates / 5.0), "updates": updates})
        rows.sort(key=lambda row: abs(float(row["effective_weight"])), reverse=True)
        return rows[: max(1, min(limit, 200))]

    def provenance(self, *, domain: str = "writing", context: str | None = None, limit: int = 20) -> list[dict[str, object]]:
        key = normalize_context(context or "") if context is not None else None
        evidence = self.store.recent_evidence(domain, 500)
        if key is not None:
            evidence = [item for item in evidence if normalize_context(item.context) == key]
        return [{"id": item.id, "kind": item.kind, "domain": item.domain, "context": item.context, "source": item.source, "created_at": item.created_at, "preferred": item.payload.get("preferred"), "rejected": item.payload.get("rejected")} for item in evidence[: max(1, min(limit, 200))]]

    def taste_context(self, *, domain: str = "writing", context: str = "", limit: int = 8) -> dict[str, object]:
        profile = self.context_profile(domain=domain, context=context, limit=limit)
        evidence = self.provenance(domain=domain, context=context or None, limit=limit)
        return {"domain": domain, "context": normalize_context(context), "instructions": [preference_instruction(str(item["feature"]), str(item["direction"])) for item in profile if float(item["confidence"]) >= 0.15], "profile": profile, "evidence_ids": [str(item["id"]) for item in evidence]}
